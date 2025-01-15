# -*- coding: utf-8 -*-
# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from openpyxl.styles.builtins import percent
from sqlalchemy import PrimaryKeyConstraint

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
    amount = db.Column(db.Float, nullable=False)  # 金额
    pay_method = db.Column(db.String(20), nullable=False)  # 支付方式

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
            'amount': self.amount,
            'pay_method': self.pay_method,
        }

class MonthlyExpCategory(db.Model):
    __tablename__ = 'monthly_exp_category'
    month = db.Column(db.String(7), nullable=False)
    category = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    percent = db.Column(db.Numeric(precision=41, scale=6), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('month', 'category'),
    )
    def to_dict(self):
        return {
            'month': self.month,
            'category': self.category,
            'amount': self.amount,
            'percent': self.percent
        }


# class MonthlyExpCDF(db.Model):
#     __tablename__ = 'monthly_exp_cdf'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     month = db.Column(db.String(7), nullable=False)
#     exp_income = db.Column(db.String(10), nullable=False)
#     category = db.Column(db.String(128), nullable=False)
#     amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
#     percent = db.Column(db.Numeric(precision=19, scale=2), nullable=False)
#     cdf = db.Column(db.Numeric(precision=41, scale=2), nullable=False)
#     counterparty = db.Column(db.String(128), nullable=False)
#     goods = db.Column(db.String(128), nullable=False)
#
#     __table_args__ = (
#         PrimaryKeyConstraint('month', 'exp_income', 'category'),
#     )
#
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'month': self.month,
#             'exp_income': self.exp_income,
#             'category': self.category,
#             'amount': self.amount,
#             'percent': self.percent,
#             'cdf': self.cdf,
#             'counterparty': self.counterparty,
#             'goods': self.goods
#         }
