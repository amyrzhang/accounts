# -*- coding: utf-8 -*-
# 定义API路由
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import desc, func, or_
from datetime import datetime
import os
import random
import uuid

from model import db, Cashflow, MonthlyBalance, VQuarterlyBalance, VAnnualBalance, MonthlyExpCategory, MonthlyExpCDF, Transaction, AccountBalance, VCurrentAsset
import model
from config import Config
from uploader import load_to_df
from utils import get_last_month, format_currency, format_percentage, generate_cashflow_id
from price_getter import *
from utils import process_transaction_data, calculate_amount_quantity

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)  # 允许所有来源
db.init_app(app)


@app.route('/transactions', methods=['GET'])
def get_cashflows():
    """查询所有记录并支持分页"""
    # 获取分页参数
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))

    # 构建查询
    query = Cashflow.query

    # 应用过滤条件 月份
    if request.args:
        for param, value in request.args.items():
            if hasattr(Cashflow, param):
                if param == 'time':
                    query = query.filter(func.date_format(Cashflow.time, '%Y-%m') == value)
                else:
                    query = query.filter(getattr(Cashflow, param) == value)

    # 分页处理
    paginated_query = query.order_by(desc(Cashflow.time)).limit(page_size).offset((page_num - 1) * page_size).all()
    return jsonify({"data": [transaction.to_dict() for transaction in paginated_query], "total": query.count()})


def add_cashflow_records(data_list):
    """
    批量添加现金流记录到数据库
    
    该函数会检查每条记录是否已存在，如果不存在则创建新的现金流记录。
    记录的唯一性通过时间（精确到分钟）、借贷方向、金额和支付方式来判断。
    
    Args:
        data_list (list): 包含现金流数据的字典列表，每个字典应包含以下键：
            - time (str or datetime): 交易时间
            - debit_credit (str): 借贷方向，'收入' 或 '支出'
            - amount (float): 金额
            - payment_method (str): 支付方式
            - type (str, optional): 交易类型
            - counterparty (str, optional): 交易对手
            - goods (str, optional): 商品或服务描述
            - status (str, optional): 状态
            - category (str, optional): 分类
            - source (str, optional): 数据来源
    
    Returns:
        list: 新创建的 Cashflow 对象列表
    
    Note:
        - 如果记录已存在（根据时间、借贷方向、金额和支付方式匹配），则不会重复创建
        - 所有新创建的记录会在一个数据库事务中提交
    """
    created_transaction = []

    for data in data_list:
        time = datetime.strptime(data.get('time'), '%Y-%m-%d %H:%M:%S') if isinstance(data.get('time'), str) else data.get('time')
        debit_credit = data.get('debit_credit')
        amount = data.get('amount')
        payment_method = data.get('payment_method')

        # 查询是否存在相同记录
        existing_transaction = Cashflow.query.filter(
            func.date_format(Cashflow.time, '%Y-%m-%d %H:%i') == time.strftime('%Y-%m-%d %H:%M'),
            Cashflow.debit_credit == debit_credit,
            Cashflow.amount == amount,
            Cashflow.payment_method == payment_method
        ).first()

        if not existing_transaction:
            transaction = Cashflow(
                cashflow_id=generate_cashflow_id(),
                time=time,
                type=data.get('type'),
                counterparty=data.get('counterparty'),
                goods=data.get('goods'),
                debit_credit=debit_credit,
                amount=amount,
                payment_method=payment_method,
                status=data.get('status'),
                category=data.get('category'),
                source=data.get('source'),
            )
            db.session.add(transaction)
            created_transaction.append(transaction)

    db.session.commit()
    return created_transaction


@app.route('/transactions', methods=['POST'])
def create_cashflow():
    """增加 cashflow 记录"""
    data_list = request.get_json()
    created_transaction = add_cashflow_records(data_list)
    return jsonify({
        "cashflow_id": [t.cashflow_id for t in created_transaction],
        "message": "Cashflow created successfully"
    }), 201


@app.route('/transactions/<string:cashflow_id>', methods=['DELETE'])
def delete_cashflow(cashflow_id):
    """根据 cashflow_id 删除所有相关记录"""
    try:
        # 查询所有 cashflow_id 匹配的记录
        transactions = Cashflow.query.filter_by(cashflow_id=cashflow_id).all()

        if not transactions:
            return jsonify({"error": "No records found with the given cashflow_id"}), 404

        # 删除所有匹配的记录
        for transaction in transactions:
            db.session.delete(transaction)

        # 提交事务
        db.session.commit()
        return f'f{cashflow_id} deleted successfully', 204  # 返回空响应和状态码204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/transfer', methods=['POST'])
def create_transfer():
    data = request.get_json()
    time = data.get('time')
    from_account = data['payment_method']
    to_account = data['counterparty']
    amount = data['amount']
    type, goods = '自转账', '转账'

    # 生成唯一 cashflow_id
    cashflow_id_out = generate_cashflow_id()
    cashflow_id_in = generate_cashflow_id()
    transfer_id = uuid.uuid4().hex

    try:
        # 开启事务
        with db.session.begin():
            # 创建流出记录
            out_record = Cashflow(
                cashflow_id=cashflow_id_out,
                transfer_id=transfer_id,
                time=time,
                payment_method=from_account,
                counterparty=to_account,
                debit_credit='支出',
                amount=amount,
                type=type,
                goods=goods
            )
            db.session.add(out_record)

            # 创建流入记录
            in_record = Cashflow(
                cashflow_id=cashflow_id_in,
                transfer_id=transfer_id,
                time=time,
                payment_method=to_account,
                counterparty=from_account,
                debit_credit='收入',
                amount=amount,
                type=type,
                goods=goods
            )
            db.session.add(in_record)

        return jsonify({
            "cashflow_id_out": cashflow_id_out,
            "cashflow_id_in": cashflow_id_in,
            "transfer_id": transfer_id,
            "message": "Cashflow created successfully"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/transfer/<string:transfer_id>', methods=['GET'])
def get_transfer(transfer_id):
    records = Cashflow.query.filter(Cashflow.transfer_id == transfer_id).all()

    if not records:
        return jsonify({"error": "Cashflow not found"}), 404

    result = [rcd.to_dict() for rcd in records]
    return jsonify(result), 200


@app.route('/transfer/<string:transfer_id>', methods=['DELETE'])
def delete_transfer(transfer_id):
    try:
        # 查询所有 transfer_id 匹配的记录
        records = Cashflow.query.filter(Cashflow.transfer_id == transfer_id).all()

        if not records:
            return jsonify({"error": "Cashflow not found"}), 404

        # 删除所有匹配的记录
        for record in records:
            db.session.delete(record)
        db.session.commit()

        return jsonify("message:" f"Successfully deleted {len(records)} records"), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/transactions/<string:cashflow_id>', methods=['PUT'])
def update_cashflow(cashflow_id):
    """修改一条记录"""
    data = request.get_json()
    transaction = Cashflow.query.get_or_404(cashflow_id)

    # 遍历键值对并更新字段
    for key, value in data.items():
        if hasattr(transaction, key):
            setattr(transaction, key, value)

    db.session.commit()
    return jsonify(transaction.to_dict())


@app.route('/transactions/<string:cashflow_id>', methods=['GET'])
def get_cashflow(cashflow_id):
    """根据 ID 查询一条记录"""
    # 查询所有 cashflow_id 匹配的记录
    transactions = Cashflow.query.filter_by(cashflow_id=cashflow_id).all()

    if not transactions:
        return jsonify({"error": "No records found with the given cashflow_id"}), 404

    return jsonify([t.to_dict() for t in transactions])


@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查是否有文件在请求中
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']

    # 检查是否选择了文件
    if file.filename == '':
        return "No selected file", 400
    if file:
        file_name = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

        if os.path.exists(file_path):
            return f"File already exists: {file_name}", 409

        try:
            file.save(file_path)
            data = load_to_df(file_path)
            add_cashflow_records(data)
        except Exception as e:
            os.remove(file_path)
            return f"Error processing file: {str(e)}", 500

        return f"File saved successfully as {file_name}", 200
    return f"Invalid file as {file}", 400


@app.route('/report', methods=['GET'])
def get_monthly_report():
    records = MonthlyBalance.query.filter(
        MonthlyBalance.month == get_last_month()
    ).with_entities(
        MonthlyBalance.income,
        MonthlyBalance.expenditure,
        MonthlyBalance.balance
    ).first()
    return jsonify({
        'expenditure': records.expenditure,
        'income': records.income,
        'balance': records.balance
    })


@app.route('/monthly/balance', methods=['GET'])
def get_monthly_balance():
    query = MonthlyBalance.query
    # 先按月份筛选
    if 'time' in request.args:
        time_length = len(request.args['time'])
        query = query.filter(func.substr(MonthlyBalance.month, 1, time_length) == request.args['time'])
    # 再按月份倒序查询
    records = query.order_by(desc(MonthlyBalance.month)).all()
    # 然后对这15条记录按月份正序排序
    records.sort(key=lambda x: x.month)
    return jsonify([rcd.to_dict() for rcd in records])


@app.route('/quarterly/balance', methods=['GET'])
def get_quarterly_balance():
    records = VQuarterlyBalance.query.all()
    return jsonify([rcd.to_dict() for rcd in records])


@app.route('/annual/balance', methods=['GET'])
def get_annual_balance():
    records = VAnnualBalance.query.all()
    return jsonify([rcd.to_dict() for rcd in records])


@app.route('/report/top10', methods=['GET'])
def get_top10_transactions():
    records = MonthlyExpCDF.query.filter(
        MonthlyExpCDF.month == get_last_month()
    ).with_entities(
        MonthlyExpCDF.counterparty,
        MonthlyExpCDF.goods,
        MonthlyExpCDF.amount,
        MonthlyExpCDF.cdf
    ).limit(10).all()
    return jsonify(
        [{
            'amount': rcd.amount,
            'goods': rcd.counterparty + ', ' + rcd.goods,
            'cdf': format_percentage(rcd.cdf)
        } for rcd in records]
    )


@app.route('/report/category', methods=['GET'])
def get_category_report():
    records = MonthlyExpCategory.query.filter(
        MonthlyExpCategory.month == get_last_month()
    ).with_entities(
        MonthlyExpCategory.category,
        MonthlyExpCategory.amount,
        MonthlyExpCategory.percent
    ).all()
    return jsonify(
        [{
            'amount': format_currency(rcd.amount),
            'category': rcd.category,
            'percent': format_percentage(rcd.percent)
        } for rcd in records]
    )


@app.route('/account/activity', methods=['GET'])
def get_account_activity():
    request_account = request.args.get('account_name')
    query = model.AccountActivity.query
    result = query.filter(model.AccountActivity.account_name == request_account).all()
    return jsonify([r.to_dict() for r in result])


@app.route('/account/balance', methods=['GET'])
def get_account_balance():
    result = model.AccountBalance.query.with_entities(
        AccountBalance.account_name,
        AccountBalance.account_type,
        AccountBalance.balance,
        AccountBalance.percent,
        AccountBalance.credit,
        AccountBalance.debit
    ).all()
    return jsonify([{
        'account_name': r.account_name,
        'account_type': r.account_type,
        'balance': r.balance,
        'percent': format_percentage(r.percent),
        'credit': r.credit,
        'debit': r.debit
    } for r in result])


@app.route('/trans', methods=['POST'])
def create_transaction():
    """
    创建交易记录（保持原有数据库操作）
    请求参数：
    [
        {
            "stock_code": "股票代码，如 000001",
            "type": "交易类型，BUY 或 SELL",
            "timestamp": "交易时间，格式为 YYYY-MM-DD HH:MM:SS",
            "price": "交易价格，数值类型",
            "fee": "手续费，数值类型"
            "amount": "金额，数值类型"
        }
    ]
    """
    data_list = request.get_json()
    created_ids = []
    errors = []

    for data in data_list:
        # 处理交易数据，计算数量、金额等字段
        processed_data, error_response = process_transaction_data(data)

        # 如果处理过程中出现错误，则记录错误信息并跳过当前记录
        if error_response:
            errors.append(error_response)
            continue

        try:
            # 开启数据库事务，确保数据一致性
            with db.session.begin():
                # 创建 Transaction 表记录
                transaction = model.Transaction(
                    stock_code=data['stock_code'],
                    type=data['type'],
                    timestamp=data['timestamp'],
                    quantity=data['quantity'],
                    price=data['price'],
                    fee=data['fee'],
                    amount=data['amount']
                )
                db.session.add(transaction)
                db.session.flush()  # 刷新会话以生成 transaction_id

                # 创建 Cashflow 表记录并与 Transaction 表关联
                payment_method = "东方财富证券(5700)"
                cashflow_record = model.Cashflow(
                    cashflow_id=generate_cashflow_id(),
                    transaction_id=transaction.transaction_id,
                    type=processed_data['cashflow_type'],
                    category="投资理财",
                    time=data['timestamp'],
                    payment_method=payment_method,
                    counterparty=data['stock_code'],
                    debit_credit=processed_data['debit_credit'],
                    amount=data['amount']+data['fee'],
                    goods=f'股票代码:{data["stock_code"]},金额:{data["amount"]},价格:{data["price"]},数量:{data["quantity"]},费用:{data["fee"]}'
                )
                db.session.add(cashflow_record)
                # 记录成功创建的 transaction_id
                created_ids.append(transaction.transaction_id)

        except Exception as e:
            # 出现异常时回滚事务并返回错误信息
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # 如果存在处理失败的记录，则返回部分成功信息和错误详情
    if errors:
        return jsonify({
            "message": f"部分记录处理失败，成功创建 {len(created_ids)} 条",
            "errors": errors,
            "created_ids": created_ids
        }), 207

    # 所有记录都成功创建时返回成功信息
    return jsonify({"message": "Transaction created successfully", "transaction_id": created_ids})


@app.route('/trans/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """更新交易记录并级联更新现金流"""
    data = request.get_json()

    try:
        # 1. 获取原始交易记录
        transaction = Transaction.query.get_or_404(transaction_id)

        # 2. 获取关联的现金流记录
        cashflow = Cashflow.query.filter_by(transaction_id=transaction_id).first()
        if not cashflow:
            return jsonify({"error": "关联的现金流记录不存在"}), 404

        # 3. 更新交易表字段
        update_fields = []
        stock_code = data.get('stock_code', transaction.stock_code)
        timestamp = data.get('timestamp', transaction.timestamp)
        type = data.get('type', transaction.type)
        price = data.get('price', transaction.price)
        quantity = data.get('quantity', transaction.quantity)
        amount = data.get('amount', transaction.amount)
        fee = data.get('fee', transaction.fee)

        # 更新交易记录
        transaction.stock_code = stock_code
        transaction.timestamp = timestamp
        transaction.type = type
        transaction.price = price
        transaction.quantity = quantity
        transaction.amount = amount
        transaction.fee = fee

        update_fields.extend(['quantity', 'price'])

        # 更新现金流记录
        cashflow.time = timestamp
        cashflow.amount = amount
        cashflow.goods = f'股票代码:{data["stock_code"]},金额:{data["amount"]},价格:{data["price"]},数量:{data["quantity"]},费用:{data["fee"]}'
        update_fields.extend(['amount', 'goods'])

        # 4. 提交修改
        db.session.commit()

        return jsonify({
            "message": "更新成功",
            "updated_fields": update_fields,
            "transaction": transaction.to_dict(),
            "cashflow": cashflow.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/trans/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    records = model.Transaction.query.filter_by(
        transaction_id=transaction_id
    ).all()

    if not records:
        return jsonify({"error": "Transaction not found"}), 404

    result = [rcd.to_dict() for rcd in records]
    return jsonify(result), 200


@app.route('/trans', methods=['GET'])
def get_transactions():
    # 获取分页参数
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    # 构建查询
    query = model.Transaction.query
    
    # 应用过滤条件
    if request.args:
        for param, value in request.args.items():
            if hasattr(model.Transaction, param) and param not in ['pageNum', 'pageSize', 'dateRange', 'stock_code']:
                query = query.filter(getattr(model.Transaction, param) == value)
        
        # 处理时间范围参数
        start_date, end_date = request.args.get('startDate'), request.args.get('endDate')
        if start_date and end_date:
            try:
                date_begin = datetime.strptime(start_date, '%Y-%m-%d')
                date_end = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(model.Transaction.timestamp.between(date_begin, date_end))
            except ValueError:
                pass  # 如果日期格式不正确，忽略该过滤条件
        
        # 处理证券代码参数
        stock_code = request.args.get('stock_code')
        if stock_code:
            query = query.filter(model.Transaction.stock_code.like(f'%{stock_code}%'))
    
    # 分页处理
    paginated_query = query.order_by(desc(model.Transaction.timestamp)).limit(page_size).offset((page_num - 1) * page_size).all()
    return jsonify({"data": [transaction.to_dict() for transaction in paginated_query], "total": query.count()}), 200


@app.route('/trans/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        # 查询同一交易的 transaction 记录和 cashflow 记录
        transaction_record = model.Transaction.query.filter_by(
            transaction_id=transaction_id
        ).first()
        cashflow_record = model.Cashflow.query.filter_by(
            transaction_id=transaction_id
        ).first()

        if not transaction_record or not cashflow_record:
            return jsonify({"error": "Transaction not found"}), 404

        # 删除记录
        db.session.delete(transaction_record)
        db.session.delete(cashflow_record)

        # 提交事务
        db.session.commit()
        return jsonify({"message": "Transaction deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/positions', methods=['GET'])
def get_positions():
    """
    查询当前持仓信息，支持分页和排序
    返回字段: 证券代码、持仓、现价、成本、持仓盈亏、持仓盈亏比、持仓成本、现值、仓位
    支持的查询参数:
    - pageNum: 页码，默认1
    - pageSize: 每页数量，默认10
    - sortBy: 排序字段
    - sortOrder: 排序顺序 (asc/desc)
    """
    try:
        # 获取分页参数
        page_num = int(request.args.get('pageNum', 1))
        page_size = int(request.args.get('pageSize', 10))

        # 构建查询
        query = VCurrentAsset.query

        # 应用排序
        sort_by = request.args.get('sortBy', 'stock_code')
        sort_order = request.args.get('sortOrder', 'asc')

        if hasattr(VCurrentAsset, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(VCurrentAsset, sort_by).desc())
            else:
                query = query.order_by(getattr(VCurrentAsset, sort_by).asc())
        else:
            query = query.order_by(VCurrentAsset.stock_code.asc())

        # 分页处理
        paginated_query = query.limit(page_size).offset((page_num - 1) * page_size).all()
        total_count = query.count()

        # 转换为字典列表
        positions_data = [position.to_dict() for position in paginated_query]

        # 计算总现值用于计算仓位
        # 注意：这里我们需要获取所有持仓的总现值，而不是当前页的
        all_positions = VCurrentAsset.query.all()
        total_realized_value = sum(position.realized_pnl for position in all_positions)

        # 添加仓位字段（现值/总现值）
        for position in positions_data:
            if total_realized_value > 0:
                position['position_ratio'] = position['realized_pnl'] / float(total_realized_value)
            else:
                position['position_ratio'] = 0

        return jsonify({
            "data": positions_data,
            "total": total_count,
            "total_realized_value": float(total_realized_value),
            "page_num": page_num,
            "page_size": page_size
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=18080)
