# -*- coding: utf-8 -*-
# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from openpyxl.styles.builtins import percent
from sqlalchemy import PrimaryKeyConstraint

from utils import format_currency

# 创建 SQLAlchemy 对象
db = SQLAlchemy()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, nullable=False)  # 交易时间
    type = db.Column(db.String(10), nullable=True)  # 类型
    counterparty = db.Column(db.String(128), nullable=True)  # 交易对方
    goods = db.Column(db.String(128), nullable=False)  # 商品
    debit_credit = db.Column(db.String(10), nullable=False)  # 收/支
    amount = db.Column(db.Float, nullable=False)  # 金额
    payment_method = db.Column(db.String(20), nullable=False)  # 支付方式
    status = db.Column(db.String(128), nullable=True)  # 支付状态
    category = db.Column(db.String(128), nullable=True)  # 类别
    source = db.Column(db.String(128), nullable=True)  # 来源

    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': self.type,
            'counterparty': self.counterparty,
            'goods': self.goods,
            'debit_credit': self.debit_credit,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'source': self.source
        }


class MonthlyBalance(db.Model):
    month = db.Column(db.String(7), nullable=False)
    balance = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    income = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    expenditure = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    credit = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    debit = db.Column(db.Numeric(precision=32, scale=2), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('month'),
    )
    def to_dict(self):
        return {
            'month': self.month,
            'balance': self.balance,
            'income': self.income,
            'expenditure': self.expenditure,
            'credit': self.credit,
            'debit': self.debit
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


class MonthlyExpCDF(db.Model):
    __tablename__ = 'monthly_exp_cdf'
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False)
    category = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    percent = db.Column(db.Numeric(precision=19, scale=2), nullable=False)
    cdf = db.Column(db.Numeric(precision=41, scale=2), nullable=False)
    counterparty = db.Column(db.String(128), nullable=False)
    goods = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'month': self.month,
            'category': self.category,
            'amount': self.amount,
            'percent': self.percent,
            'cdf': self.cdf,
            'counterparty': self.counterparty,
            'goods': self.goods
        }


class AccountBalance(db.Model):
    __tablename__ = 'account_balance'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Numeric(precision=54, scale=2), nullable=False)
    debit = db.Column(db.Numeric(precision=54, scale=2), nullable=False)
    credit = db.Column(db.Numeric(precision=54, scale=2), nullable=False)
    create_time = db.Column(db.DateTime, nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    is_included = db.Column(db.Numeric(25), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'balance': format_currency(self.balance),
            'debit': format_currency(self.debit),
            'credit': format_currency(self.credit),
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S')
        }


class AccountActivity(db.Model):
    __tablename__ = 'account_activity'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)
    debit_credit = db.Column(db.String(10), nullable=False)
    counterparty = db.Column(db.String(128), nullable=False)
    goods = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    balance = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    account_name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    source = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S'),
            'debit_credit': self.debit_credit,
            'counterparty': self.counterparty,
            'goods': self.goods,
            'amount': format_currency(self.amount),
            'balance': format_currency(self.balance),
            'account_name': self.account_name
        }



