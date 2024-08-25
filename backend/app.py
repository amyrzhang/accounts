# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request
import pandas as pd
app = Flask(__name__)


# 示例路由：获取数据
@app.route('/api/data', methods=['GET'])
def get_data():
    # tb_data = pd.read_csv('output/record_20240701_20240731.csv')
    # json_data = tb_data.to_dict(orient='records')
    data = {
        '交易时间': '2024-07-31 08:44:57', '来源': '微信', '收/支': '支出', '金额': 10.0
    }
    return jsonify(data)


# 示例路由：处理POST请求
@app.route('/api/submit', methods=['POST'])
def submit_data():
    received_data = request.json
    print("Received data:", received_data)
    return jsonify({"message": "Data received", "status": "success"})


if __name__ == '__main__':
    app.run(debug=True)
