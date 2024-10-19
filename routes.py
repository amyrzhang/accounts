# 定义API路由
from flask import Blueprint, request, jsonify
from models import db, Transaction
from datetime import datetime

api = Blueprint('api', __name__)


@api.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.get_json()
    transaction = Transaction(
        time=datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M:%S'),
        source=data['source'],
        expenditure_income=data['expenditure_income'],
        status=data['status'],
        type=data['type'],
        category=data['category'],
        counterparty=data['counterparty'],
        goods=data['goods'],
        reversed=data['reversed'],
        amount=data['amount'],
        payment_method=data['payment_method'],
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.to_dict()), 201


@api.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = Transaction.query.all()
    return jsonify([transaction.to_dict() for transaction in transactions])


@api.route('/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())


@api.route('/transactions/<int:id>', methods=['PUT'])
def update_transaction(id):
    data = request.get_json()
    transaction = Transaction.query.get_or_404(id)
    transaction.time = datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M:%S')
    transaction.source = data['source']
    transaction.expenditure_income = data['expenditure_income']
    transaction.status = data['status']
    transaction.type = data['type']
    transaction.category = data['category']
    transaction.counterparty = data['counterparty']
    transaction.goods = data['goods']
    transaction.amount = data['amount']
    transaction.reversed = data['reversed']
    transaction.payment_method = data['payment_method']
    db.session.commit()
    return jsonify(transaction.to_dict())


@api.route('/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return '', 204
