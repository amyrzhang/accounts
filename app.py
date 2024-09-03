# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

from calculate import Analysis

app = Flask(__name__)
CORS(app)  # 允许所有来源


@app.route('/read-csv')
def read_csv():
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


# 示例路由：获取数据
@app.route('/api/data', methods=['GET'])
def get_data():
    return read_csv()


@app.route('/api/data/monthly', methods=['GET'])
def get_monthly_report():
    return jsonify(Analysis().monthly_summary)


# 示例路由：处理POST请求
@app.route('/api/submit', methods=['POST'])
def submit_data():
    received_data = request.json
    print("Received data:", received_data)
    return jsonify({"message": "Data received", "status": "success"})


if __name__ == '__main__':
    app.run(debug=True)
