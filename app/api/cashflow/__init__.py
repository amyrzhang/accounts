# -*- coding: utf-8 -*-
# app/api/cashflow/__init__.py
from flask import Blueprint
from flask_restful import Api
from .resources import CashflowListResource, CashflowResource, TransferResource, UploadResource

# 定义蓝图，URL 前缀 /api/account
cashflow_bp = Blueprint("cashflow", __name__, url_prefix='/cashflow')

# 绑定 Flask-RESTful Api 对象
api = Api(cashflow_bp)

# 注册资源（RESTful 接口）
api.add_resource(CashflowListResource, '')
api.add_resource(CashflowResource, '/<string:cashflow_id>')
api.add_resource(TransferResource, '/transfer', '/transfer/<string:transfer_id>')
api.add_resource(UploadResource, '/upload')