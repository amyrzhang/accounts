# -*- coding: utf-8 -*-
# 定义API路由
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import desc, func, extract
from datetime import datetime
import os
import random

from model import db, Cashflow, MonthlyBalance, MonthlyExpCategory, MonthlyExpCDF, Transaction
import model
from config import Config
from uploader import load_to_df
from utils import get_last_month, format_currency, format_percentage, generate_cashflow_id
from price_getter import *


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


@app.route('/transactions/<string:cashflow_id>', methods=['PUT'])
def update_cashflow(cashflow_id):
    """修改一条记录"""
    data = request.get_json()
    transaction = Cashflow.query.get_or_404(cashflow_id)

    # 检查并更新字段
    if 'time' in data:
        transaction.time = datetime.strptime(data['time'], '%Y-%m-%d %H:%M:%S')
    if 'debit_credit' in data:
        transaction.debit_credit = data['debit_credit']
    if 'amount' in data:
        transaction.amount = data['amount']
    if 'counterparty' in data:
        transaction.counterparty = data['counterparty']
    if 'payment_method' in data:
        transaction.payment_method = data['payment_method']
    if 'category' in data:
        transaction.category = data['category']
    if 'status' in data:
        transaction.status = data['status']
    if 'source' in data:
        transaction.source = data['source']

    db.session.commit()
    return jsonify(transaction.to_dict())


@app.route('/transactions/<string:cashflow_id>', methods=['GET'])
def get_cashflow(cashflow_id):
    """根据 ID 查询一条记录"""
    transaction = Cashflow.query.get_or_404(cashflow_id)
    return jsonify(transaction.to_dict())


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
    result = model.AccountBalance.query.all()
    return jsonify([r.to_dict() for r in result])

@app.route('/transfer', methods=['POST'])
def create_transfer():
    data = request.get_json()
    time = data['time']
    from_account = data['payment_method']
    to_account = data['counterparty']
    amount = data['amount']
    type, goods = '自转账', '转账'

    # 生成唯一 cashflow_id
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    random_number = str(random.getrandbits(4))
    cashflow_id = current_time + random_number

    try:
        # 开启事务
        with db.session.begin():
            # 创建流出记录
            out_record = Cashflow(
                cashflow_id=cashflow_id,
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
                cashflow_id=cashflow_id,
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
            "cashflow_id": cashflow_id,
            "message": "Cashflow created successfully"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/transfer/<string:cashflow_id>', methods=['GET'])
def get_transfer(cashflow_id):
    records = Cashflow.query.filter_by(
        cashflow_id=cashflow_id
    ).all()

    if not records:
        return jsonify({"error": "Cashflow not found"}), 404

    result = [rcd.to_dict() for rcd in records]
    return jsonify(result), 200


@app.route('/transfer/<string:cashflow_id>', methods=['DELETE'])
def delete_transfer(cashflow_id):
    try:
        # 查询同一交易的两条记录
        records = Cashflow.query.filter_by(
            cashflow_id=cashflow_id
        ).all()

        if not records:
            return jsonify({"error": "Transaction not found"}), 404

        # 删除记录
        for record in records:
            db.session.delete(record)

        # 提交事务
        db.session.commit()

        return jsonify({"message": "Transaction deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/trans', methods=['POST'])
def create_transaction():
    data_list = request.get_json()
    created_transaction = []

    for data in data_list:
        payment_method = data.get('payment_method') if data.get('payment_method') else '东方财富证券(5700)'
        if data.get('type') == 'BUY':
            debit_credit = '支出'
            type = "申购"
            amount = data.get('price') * data.get('quantity') + data.get('fee')
        else:
            debit_credit = '收入'
            type = "赎回"
            amount = data.get('price') * data.get('quantity') - data.get('fee')

        try:
            with db.session.begin():
                # 更新 transaction 表
                transaction_record = model.Transaction(
                    stock_code=data.get('stock_code'),
                    type=data.get('type'),
                    timestamp=data.get('timestamp'),
                    quantity=data.get('quantity'),
                    price=data.get('price'),
                    fee=data.get('fee')
                )
                db.session.add(transaction_record)
                db.session.flush()  # 刷新会话以生成 transaction_id

                # 更新 cashflow 表
                cashflow_record = model.Cashflow(
                    cashflow_id=generate_cashflow_id(),
                    transaction_id=transaction_record.transaction_id,  # 使用生成的 transaction_id
                    type=type,
                    category="投资理财",
                    time=data.get('timestamp'),
                    payment_method=payment_method,
                    counterparty=data.get('stock_code'),
                    debit_credit=debit_credit,
                    amount=amount,
                    goods=f'股票代码：{data.get("stock_code")}，数量：{data.get("quantity")}，价格：{data.get("price")}，费用：{data.get("fee")}，金额：{amount}'
                )
                db.session.add(cashflow_record)
                created_transaction.append(transaction_record.transaction_id)
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Transaction created successfully", "transaction_id": created_transaction})


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

        # stock_list = ['002991', '603345']
        # for stock in stock_list:
        #     insert_stock_data(stock)
        # fund_list = ['513500', '513210', '510300']
        # for fund in fund_list:
        #     insert_fund_data(fund)
        # insert_fund_data('510300')
    app.run(debug=True, host='0.0.0.0', port=18080)
