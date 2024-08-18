# 定义API路由
from flask import Blueprint, request, jsonify
from models import db, Transaction
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.get_json()
    transaction = Transaction(
        transaction_time=datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M:%S'),
        source=data['source'],
        type=data['type'],
        category=data['category'],
        counterparty=data['counterparty'],
        product=data['product'],
        amount=data['amount'],
        payment_status=data['payment_status'],
        payment_method=data['payment_method'],
        processed_amount=data.get('processed_amount'),
        write_off=data['write_off']
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
    transaction.transaction_time = datetime.strptime(data['transaction_time'], '%Y-%m-%d %H:%M:%S')
    transaction.source = data['source']
    transaction.type = data['type']
    transaction.category = data['category']
    transaction.counterparty = data['counterparty']
    transaction.product = data['product']
    transaction.amount = data['amount']
    transaction.payment_status = data['payment_status']
    transaction.payment_method = data['payment_method']
    transaction.processed_amount = data.get('processed_amount')
    transaction.write_off = data['write_off']
    db.session.commit()
    return jsonify(transaction.to_dict())

@api.route('/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return '', 204
