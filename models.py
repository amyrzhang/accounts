# 定义数据库模型
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_time = db.Column(db.DateTime, nullable=False)
    source = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(128), nullable=False)
    counterparty = db.Column(db.String(128), nullable=False)
    product = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(10), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    processed_amount = db.Column(db.Float, nullable=True)
    write_off = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_time': self.transaction_time,
            'source': self.source,
            'type': self.type,
            'category': self.category,
            'counterparty': self.counterparty,
            'product': self.product,
            'amount': self.amount,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'processed_amount': self.processed_amount,
            'write_off': self.write_off
        }
