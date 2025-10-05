# -*- coding: utf-8 -*-
# app/api/__init__.py
from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api.transaction import transaction_bp as transaction_blueprint

api_bp.register_blueprint(transaction_blueprint)