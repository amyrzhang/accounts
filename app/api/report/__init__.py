# -*- coding: utf-8 -*-
# app/api/report/__init__.py

from flask import Blueprint
from flask_restful import Api
from .resources import MonthlyReportResource, MonthlyBalanceResource, QuarterlyBalanceResource, AnnualBalanceResource, \
    Top10TransactionsResource, CategoryReportResource

# 定义蓝图，URL 前缀 /api/account
report_bp = Blueprint("report", __name__, url_prefix='/report')

# 绑定 Flask-RESTful Api 对象
api = Api(report_bp)

# 在路由配置文件中添加
api.add_resource(MonthlyReportResource, '')
api.add_resource(MonthlyBalanceResource, '/monthly/balance')
api.add_resource(QuarterlyBalanceResource, '/quarterly/balance')
api.add_resource(AnnualBalanceResource, '/annual/balance')
api.add_resource(Top10TransactionsResource, '/top10')
api.add_resource(CategoryReportResource, '/category')
