# -*- coding: utf-8 -*-
# app/models/cashflow.py
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, text

from app.extentions import db

class Cashflow(db.Model):
    cashflow_id = db.Column(db.String(36))
    transaction_id = db.Column(db.Integer, ForeignKey('transaction.transaction_id'), nullable=True)
    time = db.Column(db.DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))  # 交易时间
    type = db.Column(db.String(10), nullable=True)  # 类型
    counterparty = db.Column(db.String(128), nullable=True)  # 交易对方
    goods = db.Column(db.String(128), nullable=False)  # 商品
    debit_credit = db.Column(db.String(10), nullable=False)  # 收/支
    amount = db.Column(db.Float, nullable=False)  # 金额
    payment_method = db.Column(db.String(20), nullable=False)  # 支付方式
    status = db.Column(db.String(128), nullable=True)  # 支付状态
    category = db.Column(db.String(128), nullable=True)  # 类别
    source = db.Column(db.String(128), nullable=True)  # 来源
    transfer_id = db.Column(db.String(32), nullable=True)  # 自转账ID

    __table_args__ = (
        PrimaryKeyConstraint('cashflow_id'),
    )

    def to_dict(self):
        return {
            'cashflow_id': self.cashflow_id,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': self.type,
            'counterparty': self.counterparty,
            'goods': self.goods,
            'debit_credit': self.debit_credit,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'source': self.source,
            'transfer_id': self.transfer_id
        }
