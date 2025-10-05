# app/route.py
from datetime import datetime
from flask import Blueprint, request, jsonify

# 从 models 包导入模型
from app.models.account_monthly_balance import db, AccountMonthlyBalance

bp = Blueprint('balance', __name__)

# 获取所有记录
@bp.route('/balances', methods=['GET'])
def get_all_balances():
    balances = AccountMonthlyBalance.query.all()
    return jsonify([b.to_dict() for b in balances])

# 获取单条记录
@bp.route('/balances/<int:id>', methods=['GET'])
def get_balance(id):
    balance = AccountMonthlyBalance.query.get_or_404(id)
    return jsonify(balance.to_dict())

# 添加新记录
@bp.route('/balances', methods=['POST'])
def add_balance():
    data = request.get_json()
    try:
        new_balance = AccountMonthlyBalance(
            month_date=datetime.strptime(data['month_date'], '%Y-%m-%d').date(),
            account_name=data['account_name'],
            opening_balance=data['opening_balance'],
            closing_balance=data['closing_balance'],
            current_period_change=data['current_period_change'],
            data_source=data.get('data_source', ''),
            remark=data.get('remark', '')
        )
        db.session.add(new_balance)
        db.session.commit()
        return jsonify(new_balance.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# 更新记录
@bp.route('/balances/<int:id>', methods=['PUT'])
def update_balance(id):
    balance = AccountMonthlyBalance.query.get_or_404(id)
    data = request.get_json()
    try:
        if 'month_date' in data:
            balance.month_date = datetime.strptime(data['month_date'], '%Y-%m-%d').date()
        if 'account_name' in data:
            balance.account_name = data['account_name']
        if 'opening_balance' in data:
            balance.opening_balance = data['opening_balance']
        if 'closing_balance' in data:
            balance.closing_balance = data['closing_balance']
        if 'current_period_change' in data:
            balance.current_period_change = data['current_period_change']
        if 'data_source' in data:
            balance.data_source = data['data_source']
        if 'remark' in data:
            balance.remark = data['remark']
        db.session.commit()
        return jsonify(balance.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# 删除记录
@bp.route('/balances/<int:id>', methods=['DELETE'])
def delete_balance(id):
    balance = AccountMonthlyBalance.query.get_or_404(id)
    try:
        db.session.delete(balance)
        db.session.commit()
        return jsonify({'message': 'Record deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400