# -*- coding: utf-8 -*-
# 定义API路由
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import desc, func, extract
import pandas as pd
from datetime import datetime
import os

from models import db, Transaction, MonthlyBalance, MonthlyExpCategory, MonthlyExpCDF
import models
from config import Config
from uploader import load_to_df
from utils import get_last_month, format_currency, format_percentage


app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
CORS(app)  # 允许所有来源
db.init_app(app)


@app.route('/transactions', methods=['GET'])
def get_transactions():
    """查询所有记录"""
    query = Transaction.query
    if request.args:
        for param, value in request.args.items():
            if hasattr(Transaction, param):
                if param == 'time':
                    query = query.filter(func.date_format(Transaction.time, '%Y-%m') == value)
                else:
                    query = query.filter(getattr(Transaction, param) == value)
    transactions = query.order_by(desc(Transaction.time)).all()
    return jsonify([transaction.to_dict() for transaction in transactions])


@app.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.get_json()
    transaction = Transaction(
        time=datetime.strptime(data['time'], '%Y-%m-%d %H:%M:%S'),
        source=data['source'],
        expenditure_income=data['expenditure_income'],
        status=data['status'],
        type=data['type'],
        category=data['category'],
        counterparty=data['counterparty'],
        goods=data['goods'],
        amount=data['amount'],
        pay_method=data['pay_method'],
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.to_dict()), 200


@app.route('/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return '', 204


@app.route('/transactions/<int:id>', methods=['PUT'])
def update_transaction(id):
    data = request.get_json()
    transaction = Transaction.query.get_or_404(id)
    transaction.expenditure_income = data['expenditure_income']
    transaction.category = data['category']
    db.session.commit()
    return jsonify(transaction.to_dict())


@app.route('/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    """根据 ID 查询一条记录"""
    transaction = Transaction.query.get_or_404(id)
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
        data.to_sql('transaction', con=db.engine, if_exists='append', index=False)
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
    query = models.AccountActivity.query
    result = query.filter(models.AccountActivity.account_name == request_account).all()
    return jsonify([r.to_dict() for r in result])

@app.route('/account/balance', methods=['GET'])
def get_account_balance():
    result = models.AccountBalance.query.all()
    return jsonify([r.to_dict() for r in result])




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=18080)
