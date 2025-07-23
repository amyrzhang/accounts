# -*- coding: utf-8 -*-
# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from openpyxl.styles.builtins import percent
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, text
import akshare as ak

from utils import format_currency

# 创建 SQLAlchemy 对象
db = SQLAlchemy()


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
    fk_cashflow_id = db.Column(db.String(36), nullable=True)

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
            'fk_cashflow_id': self.fk_cashflow_id
        }


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
    percent = db.Column(db.Numeric(precision=54, scale=2), nullable=False)
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


class StockPrice(db.Model):
    __tablename__ = 'stock_price'

    stock_code = db.Column(db.String(10), nullable=False)  # 股票代码（如002991）
    date = db.Column(db.Date, nullable=False)  # 交易日
    open = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 开盘价
    high = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 最高价
    low = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 最低价
    close = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 收盘价
    volume = db.Column(db.BigInteger, nullable=False)  # 成交量（股）
    amount = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 成交额（元）
    amplitude = db.Column(db.Numeric(precision=10, scale=4), nullable=True)
    change_percentage = db.Column(db.Numeric(precision=18, scale=2), nullable=True)
    change_amount = db.Column(db.Numeric(precision=24, scale=18), nullable=True)
    turnover = db.Column(db.Numeric(precision=24, scale=18), nullable=False)  # 换手率（如0.016853）

    __table_args__ = (
        PrimaryKeyConstraint('stock_code', 'date'),  # 复合主键
        db.Index('idx_date', 'date'),  # 按日期查询优化
        db.Index('idx_stock_code', 'stock_code')  # 按股票代码查询优化
    )

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
            'quantity': self.quantity,
            'price': self.price,
            'amount': self.amount,
            'fee': self.fee
        }

