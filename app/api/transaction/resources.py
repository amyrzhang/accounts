# -*- coding: utf-8 -*-
# app/api/transaction/resources.py
from flask import request
from flask_restful import Resource
from app.extentions import db
from app.models.transaction import Transaction

class TransactionListResource(Resource):
    def get(self):
        transactions = Transaction.query.all()
        return [a.to_dict() for a in transactions]

    def post(self):
        data = request.get_json()
        stock_code = Transaction(name=data["stock_code"])
        db.session.add(stock_code)
        db.session.commit()
        return stock_code.to_dict(), 201

class TransactionResource(Resource):
    def get(self, transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        return transaction.to_dict()

    def put(self, transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        data = request.get_json()
        transaction.stock_code = data["stock_code"]
        db.session.commit()
        return transaction.to_dict()

    def delete(self, transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        db.session.delete(transaction)
        db.session.commit()
        return {"msg": "删除成功"}, 204