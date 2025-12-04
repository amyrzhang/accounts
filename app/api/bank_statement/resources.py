# -*- coding: utf-8 -*-
# app/api/bank_statement/resources.py

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError
from datetime import datetime

from app.models import BankStatementSummary
from app.extentions import db
from app.service.bank_statement_service import BankStatementService
from app.schema.bank_statement_schema import summary_schema, summaries_schema

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

        # 查询
        summary_data = BankStatementService.get_statement_cashflow_comparison(month_date, account_name)

        # 构建增强响应
        response_data = self._build_enhanced_response(summary_data)
        return response_data

    @staticmethod
    def _build_enhanced_response(items):
        """构建增强型响应结构"""
        # 原始数据序列化
        serialized_items = summaries_schema.dump(items)

        # 计算聚合数据
        filter_month_date = min(item.month_date for item in items)
        total_opening_balance = sum(float(item.opening_balance) for item in items)
        total_closing_balance = sum(float(item.closing_balance) for item in items)
        total_current_period_change = sum(float(item.current_period_change) for item in items)
        total_balance = sum(float(item.balance) for item in items)
        total_bill_diff = sum(float(item.bill_diff) for item in items)

        # 构建响应结构
        response = {
            "records": serialized_items,
            "aggregation": {
                "month_date": filter_month_date.strftime("%Y-%m-%d"), # date类型序列化
                "total_opening_balance": f"{total_opening_balance:.2f}",
                "total_closing_balance": f"{total_closing_balance:.2f}",
                "total_current_period_change": f"{total_current_period_change:.2f}",
                "total_balance": f"{total_balance:.2f}",
                "total_bill_diff": f"{total_bill_diff:.2f}",
                "record_count": len(items)
            }
        }

        return response
