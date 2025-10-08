# -*- coding: utf-8 -*-
# /app/models/asset.py
from sqlalchemy import PrimaryKeyConstraint

from app.extentions import db

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
            'balance': float(self.balance) if self.balance is not None else 0,
            'debit': float(self.debit) if self.debit is not None else 0,
            'credit': float(self.credit) if self.credit is not None else 0,
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

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'date': self.date.strftime('%Y-%m-%d'),
            'open': float(self.open) if self.open is not None else 0,
            'high': float(self.high) if self.high is not None else 0,
            'low': float(self.low) if self.low is not None else 0,
            'close': float(self.close) if self.close is not None else 0,
            'volume': float(self.volume) if self.volume is not None else 0,
            'amount': float(self.amount) if self.amount is not None else 0,
            'amplitude': float(self.amplitude) if self.amplitude is not None else 0,
            'change_percentage': float(self.change_percentage) if self.change_percentage is not None else 0,
            'change_amount': float(self.change_amount) if self.change_amount is not None else 0,
            'turnover': float(self.turnover) if self.turnover is not None else 0
        }


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
