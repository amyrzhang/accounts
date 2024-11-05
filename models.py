# -*- coding: utf-8 -*-
# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
# 创建 SQLAlchemy 对象
db = SQLAlchemy()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)  # 交易时间
    source = db.Column(db.String(128), nullable=False)  # 来源
    expenditure_income = db.Column(db.String(10), nullable=False)  # 收/支
    status = db.Column(db.String(10), nullable=False)  # 支付状态
    type = db.Column(db.String(10), nullable=False)  # 类型
    category = db.Column(db.String(128), nullable=False)  # 类别
    counterparty = db.Column(db.String(128), nullable=False)  # 交易对方
    goods = db.Column(db.String(128), nullable=False)  # 商品
    reversed = db.Column(db.Boolean, nullable=False, default=False)  # 是否冲账
    amount = db.Column(db.Float, nullable=False)  # 金额
    pay_method = db.Column(db.String(20), nullable=False)  # 支付方式
    processed_amount = db.Column(db.Float, nullable=True)  # 处理金额

    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time,
            'source': self.source,
            'expenditure_income': self.expenditure_income,
            'status': self.status,
            'type': self.type,
            'category': self.category,
            'counterparty': self.counterparty,
            'goods': self.goods,
            'reversed': self.reversed,
            'amount': self.amount,
            'pay_method': self.pay_method
            # 'processed_amount': self.processed_amount
        }
