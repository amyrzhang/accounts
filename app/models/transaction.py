# -*- coding: utf-8 -*-
# app/models/transaction.py
from sqlalchemy import text

from app.extentions import db

class Transaction(db.Model):
    __tablename__ = 'transaction'

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stock_code = db.Column(db.String(10), nullable=False)  # 股票代码（如 002991.SZ）
    type = db.Column(db.String(10), nullable=False)  # 交易类型
    timestamp = db.Column(db.DateTime, nullable=True, server_default=text('CURRENT_TIMESTAMP'))  # 交易时间
    quantity = db.Column(db.Numeric(precision=10, scale=2), nullable=False)  # 交易数量（股）
    price = db.Column(db.Numeric(precision=18, scale=3), nullable=False)  # 成交单价
    amount = db.Column(db.Numeric(precision=18, scale=3), nullable=False)  # 交易金额
    fee = db.Column(db.Numeric(precision=18, scale=6), nullable=False, default=0)  # 手续费

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'stock_code': self.stock_code,
            'type': self.type,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'quantity': float(self.quantity) if self.quantity is not None else None,
            'price': float(self.price) if self.price is not None else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'fee': float(self.fee) if self.fee is not None else None
        }