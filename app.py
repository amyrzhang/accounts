# -*- coding: utf-8 -*-
# 定义API路由
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import desc, func, or_
from datetime import datetime
import os
import random

from model import db, Cashflow, MonthlyBalance, VQuarterlyBalance, VAnnualBalance, MonthlyExpCategory, MonthlyExpCDF, Transaction, AccountBalance
import model
from config import Config
from uploader import load_to_df
from utils import get_last_month, format_currency, format_percentage, generate_cashflow_id
from price_getter import *
from utils import process_transaction_data

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)  # 允许所有来源
db.init_app(app)


@app.route('/transactions', methods=['GET'])
def get_cashflows():
    """查询所有记录"""
    query = Cashflow.query
    if request.args:
        for param, value in request.args.items():
            if hasattr(Cashflow, param):
                if param == 'time':
                    query = query.filter(func.date_format(Cashflow.time, '%Y-%m') == value)
                else:
                    query = query.filter(getattr(Cashflow, param) == value)
    transactions = query.order_by(desc(Cashflow.time)).all()
    return jsonify([transaction.to_dict() for transaction in transactions])


def add_cashflow_records(data_list):
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
    fk_cashflow_id = cashflow_id_out

    try:
        # 开启事务
        with db.session.begin():
            # 创建流出记录
            out_record = Cashflow(
                cashflow_id=cashflow_id_out,
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
                fk_cashflow_id=fk_cashflow_id,
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
            "group_id": fk_cashflow_id,
            "message": "Cashflow created successfully"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/transfer/<string:cashflow_id>', methods=['GET'])
def get_transfer(cashflow_id):
    records = Cashflow.query.filter(
        or_(
            Cashflow.cashflow_id == cashflow_id,
            Cashflow.fk_cashflow_id == cashflow_id
        )
    ).all()

    if not records:
        return jsonify({"error": "Cashflow not found"}), 404

    result = [rcd.to_dict() for rcd in records]
    return jsonify(result), 200


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
        file.save(file_path)
        data = load_to_df(file_path)
        created_transaction = add_cashflow_records(data)
        return f"File saved successfully as {file_name}", 200


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
    # 先按月份倒序取前15条记录
    records = MonthlyBalance.query.order_by(desc(MonthlyBalance.month)).limit(15).all()
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
            'amount': format_currency(rcd.amount),
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
        'balance': format_currency(r.balance),
        'percent': format_percentage(r.percent),
        'credit': format_currency(r.credit),
        'debit': format_currency(r.debit)
    } for r in result])


@app.route('/trans', methods=['POST'])
def create_transaction():
    """创建交易记录（保持原有数据库操作）"""
    data_list = request.get_json()
    created_ids = []
    errors = []

    for data in data_list:
        processed_data, error_response = process_transaction_data(data)

        if error_response:
            errors.append(error_response)
            continue

        try:
            with db.session.begin():
                # 更新 transaction 表
                transaction = model.Transaction(
                    stock_code=data['stock_code'],
                    type=data['type'],
                    timestamp=data['timestamp'],
                    quantity=processed_data['quantity'],
                    price=data['price'],
                    fee=processed_data['fee']
                )
                db.session.add(transaction)
                db.session.flush()  # 刷新会话以生成 transaction_id

                # 更新 cashflow 表
                cashflow_record = model.Cashflow(
                    cashflow_id=generate_cashflow_id(),
                    transaction_id=transaction.transaction_id,
                    type=processed_data['cashflow_type'],
                    category="投资理财",
                    time=data['timestamp'],
                    payment_method=processed_data['payment_method'],
                    counterparty=data['stock_code'],
                    debit_credit=processed_data['debit_credit'],
                    amount=processed_data['amount'],
                    goods=f'股票代码：{data["stock_code"]}，数量：{processed_data["quantity"]}，价格：{data["price"]}，费用：{processed_data["fee"]}，金额：{processed_data["amount"]}'
                )
                db.session.add(cashflow_record)
                created_ids.append(transaction.transaction_id)

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    if errors:
        return jsonify({
            "message": f"部分记录处理失败，成功创建 {len(created_ids)} 条",
            "errors": errors,
            "created_ids": created_ids
        }), 207

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
        if 'quantity' in data or 'price' in data:
            # 计算新金额（保持原有逻辑）
            new_quantity = data.get('quantity', transaction.quantity)
            new_price = data.get('price', transaction.price)

            if transaction.type == 'BUY':
                new_amount = round(float(new_price) * float(new_quantity) + float(transaction.fee), 2)
            else:
                new_amount = round(float(new_price) * float(new_quantity) - float(transaction.fee), 2)

            # 更新交易记录
            transaction.quantity = new_quantity
            transaction.price = new_price
            update_fields.extend(['quantity', 'price'])

            # 更新现金流记录
            cashflow.amount = new_amount
            cashflow.goods = (
                f'股票代码：{transaction.stock_code}，'
                f'数量：{new_quantity}，'
                f'价格：{new_price}，'
                f'费用：{transaction.fee}，'
                f'金额：{new_amount}'
            )
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=18080)
