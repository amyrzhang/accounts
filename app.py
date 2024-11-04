# -*- coding: utf-8 -*-
# 定义API路由
from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

from models import db, Transaction
from config import Config
from query import Analyzer
from uploader import write_db
from utils import format_currency, format_percentage

api = Blueprint('api', __name__)
app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)  # 允许所有来源
db.init_app(app)


# @app.route('/api/data', methods=['GET'])
# def get_transactions():
#     a = Analyzer()
#     a.rename()
#     if request.args:
#         a.filter(params=request.args)
#     return jsonify(a.df.to_dict(orient='records'))

@app.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = Transaction.query.all()
    return jsonify([transaction.to_dict() for transaction in transactions])

@app.route('/api/report', methods=['GET'])
def get_monthly_report():
    a = Analyzer()
    a.filter_monthly()
    return jsonify({
        'expenditure': -a.sums['支出'],
        'income': a.sums['收入'],
        'balance': a.sums.sum()
    })


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


@app.route('/api/report/top10', methods=['GET'])
def get_top10_transactions():
    a = Analyzer()
    a.filter_monthly()
    res = a.top10_transactions
    res['金额'] = res['金额'].apply(format_currency)
    res['cdf'] = res['cdf'].apply(format_percentage)
    return jsonify(res.to_dict(orient='records'))


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
        write_db(file_path)
        return f"File saved successfully as {file_name}", 200


# @api.route('/transactions', methods=['POST'])
# def create_transaction():
#     data = request.get_json()
#     transaction = Transaction(
#         time=datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M:%S'),
#         source=data['source'],
#         expenditure_income=data['expenditure_income'],
#         status=data['status'],
#         type=data['type'],
#         category=data['category'],
#         counterparty=data['counterparty'],
#         goods=data['goods'],
#         reversed=data['reversed'],
#         amount=data['amount'],
#         payment_method=data['payment_method'],
#     )
#     db.session.add(transaction)
#     db.session.commit()
#     return jsonify(transaction.to_dict()), 201





# @api.route('/transactions/<int:id>', methods=['GET'])
# def get_transaction(id):
#     transaction = Transaction.query.get_or_404(id)
#     return jsonify(transaction.to_dict())
#
#
# @api.route('/transactions/<int:id>', methods=['PUT'])
# def update_transaction(id):
#     data = request.get_json()
#     transaction = Transaction.query.get_or_404(id)
#     transaction.time = datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M:%S')
#     transaction.source = data['source']
#     transaction.expenditure_income = data['expenditure_income']
#     transaction.status = data['status']
#     transaction.type = data['type']
#     transaction.category = data['category']
#     transaction.counterparty = data['counterparty']
#     transaction.goods = data['goods']
#     transaction.amount = data['amount']
#     transaction.reversed = data['reversed']
#     transaction.payment_method = data['payment_method']
#     db.session.commit()
#     return jsonify(transaction.to_dict())
#
#
# @api.route('/transactions/<int:id>', methods=['DELETE'])
# def delete_transaction(id):
#     transaction = Transaction.query.get_or_404(id)
#     db.session.delete(transaction)
#     db.session.commit()
#     return '', 204


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=18080)
