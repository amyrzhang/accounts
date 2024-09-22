# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import re

from calculate import Analyzer
from uploader import WeixinProcessor
from uploader import write_db

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)  # 允许所有来源


@app.route('/api/data', methods=['GET'])
def get_transactions():
    df = pd.read_csv(
        'output/transaction_record.csv',
        encoding='utf-8',
        usecols=range(11)
    )
    if request.args.get('month'):
        df = df[df['交易时间'].str.contains(request.args.get('month'))]
    df.sort_values(by='交易时间', ascending=False, inplace=True)
    df.rename(
        inplace=True,
        columns={
            '交易时间': 'time',
            '来源': 'source',
            '收/支': 'expenditure_income',
            '支付状态': 'status',
            '类型': 'type',
            'category': 'category',
            '交易对方': 'counterparty',
            '商品': 'goods',
            '是否冲账': 'reversed',
            '金额': 'amount',
            '支付方式': 'pay_method'
        },
    )
    return jsonify(df.to_dict(orient='records'))


@app.route('/api/report', methods=['GET'])
def get_monthly_report():
    a = Analyzer()
    return jsonify({
        'expenditure': -a.sums['支出'],
        'income': a.sums['收入'],
        'balance': a.sums.sum()
    })


@app.route('/api/report/category', methods=['GET'])
def get_category_report():
    return jsonify(Analyzer().category_sums['支出'].abs().sort_values(ascending=False).to_dict())


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


if __name__ == '__main__':
    app.run(debug=True)
