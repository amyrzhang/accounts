# -*- coding: utf-8 -*-
# app/api/bank_statement/resources.py
from marshmallow import Schema, fields, validate
from datetime import datetime

# ====================
# 数据校验 Schema（Marshmallow）
# ====================
class BankStatementSummarySchema(Schema):
    id = fields.Integer(dump_only=True)  # 只读
    month_date = fields.Date(required=True, format="%Y-%m-%d",
                             validate=validate.Range(min=datetime(2000, 1, 1).date(),
                                                    error="月份日期不能早于2000-01-01"))
    account_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    opening_balance = fields.Decimal(required=True, places=2, as_string=True)
    closing_balance = fields.Decimal(required=True, places=2, as_string=True)
    current_period_change = fields.Decimal(required=True, places=2, as_string=True)
    remark = fields.String(validate=validate.Length(max=500))

summary_schema = BankStatementSummarySchema()

class BankStatementSummariesSchema(Schema):
    id = fields.Integer(dump_only=True)  # 只读
    month_date = fields.Date(required=True, format="%Y-%m-%d",
                             validate=validate.Range(min=datetime(2000, 1, 1).date(),
                                                    error="月份日期不能早于2000-01-01"))
    account_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    opening_balance = fields.Decimal(required=True, places=2, as_string=True)
    closing_balance = fields.Decimal(required=True, places=2, as_string=True)
    current_period_change = fields.Decimal(required=True, places=2, as_string=True)
    balance = fields.Decimal(required=True, places=2, as_string=True)
    bill_diff = fields.Decimal(required=True, places=2, as_string=True)

summaries_schema = BankStatementSummariesSchema(many=True)
