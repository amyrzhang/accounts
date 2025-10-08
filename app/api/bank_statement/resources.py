# -*- coding: utf-8 -*-
# app/api/bank_statement/resources.py

from sqlalchemy import func
from flask import request
from flask_restful import Resource
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

from app.models import BankStatementSummary  # 假设 models.py 里有上面的 Model
from app.extentions import db


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
    remark = fields.String(allow_none=True, validate=validate.Length(max=200))
    create_time = fields.DateTime(dump_only=True)  # 只读
    update_time = fields.DateTime(dump_only=True)  # 只读

summary_schema = BankStatementSummarySchema()
summaries_schema = BankStatementSummarySchema(many=True)

# ====================
# RESTful 资源类
# ====================
class BankStatementSummaryResource(Resource):
    """单条记录操作（GET / PUT / DELETE）"""
    def get(self, id):
        """获取单条记录"""
        item = BankStatementSummary.query.get_or_404(id)
        return summary_schema.dump(item)

    def put(self, id):
        """更新记录"""
        item = BankStatementSummary.query.get_or_404(id)
        try:
            data = summary_schema.load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400

        for key, value in data.items():
            setattr(item, key, value)

        item.update_time = datetime.now()
        db.session.commit()
        return summary_schema.dump(item)

    def delete(self, id):
        """删除记录"""
        item = BankStatementSummary.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "删除成功"}, 200


class BankStatementSummaryListResource(Resource):
    """多条记录操作（GET / POST）"""
    def get(self):
        """获取记录列表（支持按月份和账户名过滤）"""
        month_date = request.args.get("month_date")
        account_name = request.args.get("account_name")

        query = BankStatementSummary.query
        if month_date:
            query = query.filter_by(month_date=month_date)
        if account_name:
            query = query.filter_by(account_name=account_name)

        items = query.all()
        return summaries_schema.dump(items)

    def post(self):
        """新增记录"""
        try:
            data = summary_schema.load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400

        new_item = BankStatementSummary(**data)
        db.session.add(new_item)
        db.session.commit()
        return summary_schema.dump(new_item), 201



# 输出数据的 Schema
class MonthlySummarySchema(Schema):
    month_date = fields.Date(required=True, format="%Y-%m-%d")
    total_opening_balance = fields.Decimal(places=2, as_string=True)
    total_closing_balance = fields.Decimal(places=2, as_string=True)
    total_current_period_change = fields.Decimal(places=2, as_string=True)

monthly_summary_schema = MonthlySummarySchema(many=True)

class BankStatementMonthlyAggResource(Resource):
    """按月汇总对账单"""
    def get(self):
        """
        按月汇总查询
        Query 参数:
            start_month: 开始月份 (YYYY-MM-DD)
            end_month: 结束月份 (YYYY-MM-DD)
        """
        start_month = request.args.get("start_month")
        end_month = request.args.get("end_month")

        # 基本查询
        query = db.session.query(
            BankStatementSummary.month_date,
            func.sum(BankStatementSummary.opening_balance).label("total_opening_balance"),
            func.sum(BankStatementSummary.closing_balance).label("total_closing_balance"),
            func.sum(BankStatementSummary.current_period_change).label("total_current_period_change")
        ).group_by(BankStatementSummary.month_date)

        # 条件过滤
        if start_month:
            try:
                start_date = datetime.strptime(start_month, "%Y-%m-%d").date()
                query = query.filter(BankStatementSummary.month_date >= start_date)
            except ValueError:
                return {"error": "start_month 格式错误，应为 YYYY-MM-DD"}, 400

        if end_month:
            try:
                end_date = datetime.strptime(end_month, "%Y-%m-%d").date()
                query = query.filter(BankStatementSummary.month_date <= end_date)
            except ValueError:
                return {"error": "end_month 格式错误，应为 YYYY-MM-DD"}, 400

        # 执行查询
        results = query.all()

        # 格式化返回
        return monthly_summary_schema.dump(results)
