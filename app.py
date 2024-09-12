# -*- coding: utf-8 -*-

from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import pandas as pd
from werkzeug.utils import secure_filename
import os

from calculate import Analysis
from loader import WeixinTransactions

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)  # 允许所有来源


@app.route('/api/data/transactions.json', methods=['GET'])
def get_transactions():
    df = pd.read_csv(
        './output/record_20240701_20240731.csv',
        encoding='utf-8',
        usecols=range(11)
    )
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


@app.route('/api/data/monthly', methods=['GET'])
def get_monthly_report():
    return jsonify(Analysis().monthly_summary)


@app.route('/api/submit', methods=['POST'])
def submit_data():
    received_data = request.json
    print("Received uploads:", received_data)
    return jsonify({"message": "Data received", "status": "success"})


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return f"File already exists: {filename}", 409
        file.save(file_path)
        wxt = WeixinTransactions(file_path)  # 写入数据
        wxt.write_data()
        return f"File saved successfully as {filename}", 200


if __name__ == '__main__':
    app.run(debug=True)
