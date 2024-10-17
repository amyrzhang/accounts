# �������ݿ�ģ��
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)  # ����ʱ��
    source = db.Column(db.String(128), nullable=False)  # ��Դ
    expenditure_income = db.Column(db.String(10), nullable=False)  # ��/֧
    status = db.Column(db.String(10), nullable=False)  # ֧��״̬
    type = db.Column(db.String(10), nullable=False)  # ����
    category = db.Column(db.String(128), nullable=False)  # ���
    counterparty = db.Column(db.String(128), nullable=False)  # ���׶Է�
    goods = db.Column(db.String(128), nullable=False)  # ��Ʒ
    reversed = db.Column(db.Boolean, nullable=False, default=False)  # �Ƿ����
    amount = db.Column(db.Float, nullable=False)  # ���
    pay_method = db.Column(db.String(20), nullable=False)  # ֧����ʽ
    # processed_amount = db.Column(db.Float, nullable=True)  # ������

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
