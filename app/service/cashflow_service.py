# -*- coding: utf-8 -*-
# app/service/cashflow_service.py
from app.extentions import db
from app.models import Cashflow
from sqlalchemy import func


class CashflowSummaryService:
    @staticmethod
    def get_account_summary(filter_month_date):
        """
        获取按月份和账户分组的现金流汇总数据

        Returns:
            list: 包含每月每个账户的收支汇总数据
        """
        # 查询所有现金流记录
        query = Cashflow.query.filter(Cashflow.transfer_id.is_(None))

        if filter_month_date:
            query = query.filter(func.date_format(Cashflow.time, '%Y-%m-01') == filter_month_date)

        # 构造month_date字段：将时间格式化为YYYY-MM-01
        month_date = func.concat(
            func.date_format(Cashflow.time, '%Y-%m'),
            '-01'
        ).label('month_date')

        # 计算收入总额：debit_credit为'收入'时的amount总和
        debit = func.sum(
            db.case((Cashflow.debit_credit == '收入', Cashflow.amount), else_=0)
        ).label('debit')

        # 计算支出总额：debit_credit为'支出'时的amount总和
        credit = func.sum(
            db.case((Cashflow.debit_credit == '支出', Cashflow.amount), else_=0)
        ).label('credit')

        # 执行查询并按month_date和payment_method分组
        summary_data = query.with_entities(
            month_date,
            Cashflow.payment_method,
            debit,
            credit,
            (debit - credit).label('balance')
        ).group_by(
            month_date,
            Cashflow.payment_method
        ).all()

        # 将查询结果转换为字典列表
        result = []
        for row in summary_data:
            result.append({
                'month_date': row.month_date,
                'payment_method': row.payment_method,
                'debit': float(row.debit) if row.debit else 0.0,
                'credit': float(row.credit) if row.credit else 0.0,
                'balance': float(row.balance) if row.balance else 0.0
            })

        return result

    @staticmethod
    def get_monthly_total_balance(filter_month_date=None):
        """
        获取按月份汇总的账户余额

        Args:
            filter_month_date (str, optional): 指定月份，格式为YYYY-MM

        Returns:
            dict or float: 指定月份的余额或所有月份的余额字典
        """
        # 查询所有现金流记录
        query = Cashflow.query.filter(Cashflow.transfer_id.is_(None))

        if filter_month_date:
            query = query.filter(func.date_format(Cashflow.time, '%Y-%m-01') == filter_month_date)

        # 构造month_date字段
        month_date = func.concat(
            func.date_format(Cashflow.time, '%Y-%m'),
            '-01'
        ).label('month_date')

        # 计算净余额：收入-支出
        net_balance = func.sum(
            db.case(
                (Cashflow.debit_credit == '收入', Cashflow.amount),
                (Cashflow.debit_credit == '支出', -Cashflow.amount),
                else_=0
            )
        ).label('net_balance')

        # 按月份分组查询
        summary_data = query.with_entities(
            month_date,
            net_balance
        ).group_by(month_date).all()

        result = {}
        for row in summary_data:
            result[row.month_date] = float(row.net_balance) if row.net_balance else 0.0
        return result
