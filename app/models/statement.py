# -*- coding: utf-8 -*-
from sqlalchemy import PrimaryKeyConstraint

from app.utils.utils import format_currency
from app.extentions import db


class BaseBalance(db.Model):
    __abstract__ = True  # 声明为抽象类，不会创建表

    balance = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    income = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    expenditure = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    credit = db.Column(db.Numeric(precision=32, scale=2), nullable=False)
    debit = db.Column(db.Numeric(precision=32, scale=2), nullable=False)

    def to_dict(self):
        return {
            'balance': format_currency(self.balance),
            'income': format_currency(self.income),
            'expenditure': format_currency(self.expenditure),
            'credit': format_currency(self.credit),
            'debit': format_currency(self.debit)
        }


class MonthlyBalance(BaseBalance):
    month = db.Column(db.String(7), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('month'),
    )

    def to_dict(self):
        result = super().to_dict()
        result['month'] = self.month
        return result


class VQuarterlyBalance(BaseBalance):
    month = db.Column(db.String(7), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('month'),
    )

    def to_dict(self):
        result = super().to_dict()
        result['month'] = self.month
        return result


class VAnnualBalance(BaseBalance):
    month = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('month'),
    )

    def to_dict(self):
        result = super().to_dict()
        result['month'] = self.month
        return result


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
            'amount': float(self.amount),
            'percent': float(self.percent)
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
