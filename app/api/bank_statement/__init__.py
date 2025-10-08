# -*- coding: utf-8 -*-
# app/api/bank_statement/__init__.py
from flask import Blueprint
from flask_restful import Api
from .resources import BankStatementSummaryListResource, BankStatementSummaryResource, BankStatementMonthlyAggResource

# 定义蓝图，URL 前缀 /api/account
bank_statement_summary_bp = Blueprint("bank-statement-summary", __name__, url_prefix='/bank-statement')

# 绑定 Flask-RESTful Api 对象
api = Api(bank_statement_summary_bp)

# 注册资源（RESTful 接口）
api.add_resource(BankStatementSummaryListResource, '')
api.add_resource(BankStatementSummaryResource, '/<int:id>')
api.add_resource(BankStatementMonthlyAggResource, '/monthly-agg')
