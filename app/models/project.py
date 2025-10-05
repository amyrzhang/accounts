# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


# 创建 SQLAlchemy 对象
db = SQLAlchemy()


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('income', 'expenditure'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }