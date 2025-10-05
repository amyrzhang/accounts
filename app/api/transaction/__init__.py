# app/api/account/__init__.py
from flask import Blueprint
from flask_restful import Api
from .resources import TransactionListResource, TransactionResource

# ������ͼ��URL ǰ׺ /api/account
transaction_bp = Blueprint("transaction", __name__, url_prefix='/transaction')

# �� Flask-RESTful Api ����
api = Api(transaction_bp)

# ע����Դ��RESTful �ӿڣ�
api.add_resource(TransactionListResource, "")       # /api/transaction
api.add_resource(TransactionResource, "/<int:transaction_id>")  # /api/transaction/<id>