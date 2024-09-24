# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import re

from query import Analyzer
from uploader import WeixinProcessor
from uploader import write_db
from pprint import pprint

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)  # 允许所有来源


@app.route('/api/data', methods=['GET'])
def get_transactions():
    a = Analyzer()
    a.rename()
    print(a.df.head(2))
    if request.args:
        a.filter(params=request.args)
    return jsonify(a.df.to_dict(orient='records'))


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
    return jsonify(a.account_sums.reset_index().to_dict(orient='records'))


@app.route('/api/report/top10', methods=['GET'])
def get_top10_transactions():
    a = Analyzer()
    a.filter_monthly()
    return jsonify(a.top10_transactions.to_dict(orient='records'))


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
