# -*- coding: utf-8 -*-
# app/api/account/__init__.py
from flask import Blueprint
from flask_restful import Api
from .resources import TransactionListResource, TransactionResource

# 定义蓝图，URL 前缀 /api/account
transaction_bp = Blueprint("transaction", __name__, url_prefix='/transaction')

# 绑定 Flask-RESTful Api 对象
api = Api(transaction_bp)

# 注册资源（RESTful 接口）
api.add_resource(TransactionListResource, "")       # /api/transaction
api.add_resource(TransactionResource, "/<int:transaction_id>")  # /api/transaction/<id>