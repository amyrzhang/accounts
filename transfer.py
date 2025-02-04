#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import datetime
import random

from config import Config
from model import db, Cashflow

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


@app.route('/transfer', methods=['POST'])
def create_transfer():
    data = request.get_json()
    time = data['time']
    from_account = data['payment_method']
    to_account = data['counterparty']
    amount = data['amount']
    type, goods = '自转账', '转账'

    # 生成唯一 cashflow_id
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
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
            "message": "Transaction created successfully"
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
        return jsonify({"error": "Transaction not found"}), 404

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=18080)