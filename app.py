# -*- coding: utf-8 -*-
# 定义API路由
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import desc, func, extract
import pandas as pd
from datetime import datetime
import os

from models import db, Transaction, MonthlyTransaction
from config import Config
from query import Analyzer
from uploader import load_to_df
from utils import format_currency, format_percentage


app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
CORS(app)  # 允许所有来源
db.init_app(app)


@app.route('/transactions', methods=['GET'])
def get_transactions():
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
        reversed=data['reversed'],
        amount=data['amount'],
        pay_method=data['pay_method'],
        processed_amount=data['amount']
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
    transaction.reversed = data['reversed']
    db.session.commit()
    return jsonify(transaction.to_dict())


@app.route('/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
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


@app.route('/api/report', methods=['GET'])
def get_monthly_report():
    subquery = Transaction.query.with_entities(
        func.max(extract('year', Transaction.time)).label('max_year'),
        func.max(extract('month', Transaction.time)).label('max_month')
    ).subquery()
    transactions = Transaction.query.filter(
        extract('year', Transaction.time) == subquery.c.max_year,
        extract('month', Transaction.time) == subquery.c.max_month
    ).all()
    income_sum = sum([transaction.amount for transaction in transactions if transaction.expenditure_income == '收入'])
    expenditure_sum = sum([transaction.amount for transaction in transactions if transaction.expenditure_income == '支出'])
    return jsonify({
        'expenditure': expenditure_sum,
        'income': income_sum,
        'balance': income_sum - expenditure_sum
    })


@app.route('/api/report/top10', methods=['GET'])
def get_top10_transactions():
    transactions = MonthlyTransaction.query.with_entities(
        MonthlyTransaction.goods,
        MonthlyTransaction.amount,
        MonthlyTransaction.cdf
    ).limit(10).all()
    return jsonify(
        [{
            'amount': format_currency(transaction.amount),
            'goods': transaction.goods,
            'cdf': format_percentage(transaction.cdf)
        } for transaction in transactions]
    )


@app.route('/api/report/category', methods=['GET'])
def get_category_report():
    a = Analyzer()
    a.filter_monthly()
    return jsonify(a.category_sums['支出'].abs().sort_values(ascending=False).to_dict())


@app.route('/api/report/account', methods=['GET'])
def get_account_report():
    a = Analyzer()
    a.filter_monthly()
    res = a.account_sums
    return jsonify(res.reset_index().to_dict(orient='records'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=18080)
