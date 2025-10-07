# -*- coding: utf-8 -*-
# app/api/asset/__init__.py
from flask import Blueprint
from flask_restful import Api
from .resources import AccountBalanceResource, PositionListResource, AccountBalanceListResource

# 定义蓝图，URL 前缀 /api/account
asset_bp = Blueprint("asset", __name__, url_prefix='/asset')

# 绑定 Flask-RESTful Api 对象
api = Api(asset_bp)

# 注册资源（RESTful 接口）
api.add_resource(AccountBalanceResource, '/balance')
api.add_resource(PositionListResource, '/position')
api.add_resource(AccountBalanceListResource, '/balances')
# api.add_resource(AccountBalanceResource, '/balances/<int:id>')
