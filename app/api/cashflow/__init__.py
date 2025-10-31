# app/api/cashflow/__init__.py
from flask import Blueprint
from flask_restful import Api
from .resources import CashflowListResource, CashflowResource, TransferResource, UploadResource

# ������ͼ��URL ǰ׺ /api/account
cashflow_bp = Blueprint("cashflow", __name__, url_prefix='/cashflow')

# �� Flask-RESTful Api ����
api = Api(cashflow_bp)

# ע����Դ��RESTful �ӿڣ�
api.add_resource(CashflowListResource, '')
api.add_resource(CashflowResource, '/<string:cashflow_id>')
api.add_resource(TransferResource, '/transfer', '/transfer/<string:transfer_id>')
api.add_resource(UploadResource, '/upload')