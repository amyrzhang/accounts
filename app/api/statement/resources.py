# -*- coding: utf-8 -*-
# app/api/statement/resources.py
from flask import request
from flask_restful import Resource
from sqlalchemy import desc, func

from app.models import MonthlyExpCategory, MonthlyExpCDF, VAnnualBalance, VQuarterlyBalance, MonthlyBalance
from app.utils.utils import get_last_month, format_currency, format_percentage


class MonthlyReportResource(Resource):
    """月度报告资源"""

    def get(self):
        """获取月度收支报告"""
        records = MonthlyBalance.query.filter(
            MonthlyBalance.month == get_last_month()
        ).with_entities(
            MonthlyBalance.income,
            MonthlyBalance.expenditure,
            MonthlyBalance.balance
        ).first()
        return records.to_dict(), 200


class MonthlyBalanceResource(Resource):
    """月度余额资源"""

    def get(self):
        """获取月度余额数据"""
        query = MonthlyBalance.query
        # 先按月份筛选
        if 'time' in request.args:
            time_length = len(request.args['time'])
            query = query.filter(func.substr(MonthlyBalance.month, 1, time_length) == request.args['time'])
        # 再按月份倒序查询
        records = query.order_by(desc(MonthlyBalance.month)).all()
        # 然后对这15条记录按月份正序排序
        records.sort(key=lambda x: x.month)
        return [rcd.to_dict() for rcd in records], 200


class QuarterlyBalanceResource(Resource):
    """季度余额资源"""

    def get(self):
        """获取季度余额数据"""
        records = VQuarterlyBalance.query.all()
        return [rcd.to_dict() for rcd in records], 200


class AnnualBalanceResource(Resource):
    """年度余额资源"""

    def get(self):
        """获取年度余额数据"""
        records = VAnnualBalance.query.all()
        return [rcd.to_dict() for rcd in records], 200


class Top10TransactionsResource(Resource):
    """Top10交易资源"""

    def get(self):
        """获取Top10支出交易"""
        records = MonthlyExpCDF.query.filter(
            MonthlyExpCDF.month == get_last_month()
        ).with_entities(
            MonthlyExpCDF.counterparty,
            MonthlyExpCDF.goods,
            MonthlyExpCDF.amount,
            MonthlyExpCDF.cdf
        ).limit(10).all()
        return [{
            'amount': rcd.amount,
            'goods': rcd.counterparty + ', ' + rcd.goods,
            'cdf': format_percentage(rcd.cdf)
        } for rcd in records], 200


class CategoryReportResource(Resource):
    """分类报告资源"""

    def get(self):
        """获取支出分类报告"""
        records = MonthlyExpCategory.query.filter(
            MonthlyExpCategory.month == get_last_month()
        ).with_entities(
            MonthlyExpCategory.category,
            MonthlyExpCategory.amount,
            MonthlyExpCategory.percent
        ).all()
        return [{
            'amount': format_currency(rcd.amount),
            'category': rcd.category,
            'percent': format_percentage(rcd.percent)
        } for rcd in records], 200
