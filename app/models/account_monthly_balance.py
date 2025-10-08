# models/account_monthly_balance.py
from datetime import datetime
from app.extentions import db

class AccountMonthlyBalance(db.Model):
    __tablename__ = 'account_monthly_balance'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='记录唯一ID')
    month_date = db.Column(db.Date, nullable=False, comment='数据所属月份（YYYY-MM-01）')
    account_name = db.Column(db.String(100), nullable=False, comment='账户名称')
    opening_balance = db.Column(db.Numeric(18, 2), nullable=False, comment='期初余额（元）')
    closing_balance = db.Column(db.Numeric(18, 2), nullable=False, comment='期末余额（元）')
    current_period_change = db.Column(db.Numeric(18, 2), nullable=False, comment='当期变动金额（元）')
    data_source = db.Column(db.String(50), default='', comment='数据来源')
    remark = db.Column(db.String(200), default='', comment='备注')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        db.UniqueConstraint('month_date', 'account_name', name='uk_month_account'),
        db.Index('idx_month', 'month_date'),
        db.Index('idx_account_name', 'account_name'),
        {'comment': '账户月度余额及变动记录表'}
    )

    def to_dict(self):
        return {
            'id': self.id,
            'month_date': self.month_date.strftime('%Y-%m-%d'),
            'account_name': self.account_name,
            'opening_balance': float(self.opening_balance),
            'closing_balance': float(self.closing_balance),
            'current_period_change': float(self.current_period_change),
            'data_source': self.data_source,
            'remark': self.remark,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S')
        }