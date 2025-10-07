# -*- coding: utf-8 -*-
# app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api.transaction import transaction_bp as transaction_blueprint
from app.api.cashflow import cashflow_bp as cashflow_blueprint
from app.api.asset import asset_bp as asset_blueprint
from app.api.report import report_bp as report_blueprint

api_bp.register_blueprint(transaction_blueprint)
api_bp.register_blueprint(cashflow_blueprint)
api_bp.register_blueprint(asset_blueprint)
api_bp.register_blueprint(report_blueprint)