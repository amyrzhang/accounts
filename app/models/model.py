# -*- coding: utf-8 -*-
# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, text

from app.utils.utils import format_currency

# 创建 SQLAlchemy 对象
db = SQLAlchemy()


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
            'balance': self.balance,
            'debit': self.debit,
            'credit': self.credit,
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


class VCurrentAsset(db.Model):
    __tablename__ = 'v_current_asset'

    stock_code = db.Column(db.String(10), primary_key=True, nullable=False)  # 证券代码
    quantity = db.Column(db.Numeric(precision=10, scale=2), nullable=False)  # 持仓数量
    price = db.Column(db.Numeric(precision=18, scale=3), nullable=False)  # 现价
    avg_cost = db.Column(db.Numeric(precision=18, scale=3), nullable=False)  # 成本
    unrealized_pnl = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 持仓盈亏
    pnl_ratio = db.Column(db.Numeric(precision=10, scale=4), nullable=False)  # 持仓盈亏比
    position_value = db.Column(db.Numeric(precision=18, scale=2), nullable=False)  # 持仓成本
    realized_pnl = db.Column(db.Numeric(precision=18, scale=2), nullable=True)  # 实现盈亏（可能为NULL）

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'quantity': float(self.quantity) if self.quantity is not None else 0,
            'price': float(self.price) if self.price is not None else 0,
            'avg_cost': float(self.avg_cost) if self.avg_cost is not None else 0,
            'unrealized_pnl': float(self.unrealized_pnl) if self.unrealized_pnl is not None else 0,
            'pnl_ratio': float(self.pnl_ratio) if self.pnl_ratio is not None else 0,
            'position_value': float(self.position_value) if self.position_value is not None else 0,
            'realized_pnl': float(self.realized_pnl) if self.realized_pnl is not None else 0
        }
