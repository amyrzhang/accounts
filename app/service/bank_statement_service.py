# -*- coding: utf-8 -*-
# app/service/bank_statement_service.py
from app.extentions import db
from app.models import Cashflow, BankStatementSummary
from sqlalchemy import func


class BankStatementService:
    @staticmethod
    def get_statement_cashflow_comparison(month_date=None, account_name=None):
        """
        获取银行对账单与现金流数据的对比结果

        Args:
            month_date (str, optional): 月份筛选，格式为 YYYY-MM-01
            account_name (str: optional): 账户名称筛选
        """
        # 子查询：现金流按月份和支付方式分组汇总
        cashflow_subquery = db.session.query(
            func.date_format(Cashflow.time, '%Y-%m-01').label('month_date'),
            Cashflow.payment_method,
            func.sum(
                db.case((Cashflow.debit_credit == '收入', Cashflow.amount), else_=0)
            ).label('debit'),
            func.sum(
                db.case((Cashflow.debit_credit == '支出', Cashflow.amount), else_=0)
            ).label('credit'),
            (
                    func.sum(
                        db.case((Cashflow.debit_credit == '收入', Cashflow.amount), else_=0)
                    ) -
                    func.sum(
                        db.case((Cashflow.debit_credit == '支出', Cashflow.amount), else_=0)
                    )
            ).label('balance')
        ).filter(
            Cashflow.transaction_id.is_(None)  # 过滤掉证券交易
        ).group_by(
            func.date_format(Cashflow.time, '%Y-%m-01'),
            Cashflow.payment_method
        ).subquery()

        # 主查询：连接银行对账单和现金流汇总数据
        main_query = db.session.query(
            BankStatementSummary.id,
            BankStatementSummary.month_date,
            BankStatementSummary.account_name,
            BankStatementSummary.opening_balance,
            BankStatementSummary.closing_balance,
            BankStatementSummary.current_period_change,
            cashflow_subquery.c.balance,
            (
                    BankStatementSummary.current_period_change - cashflow_subquery.c.balance
            ).label('bill_diff')
        ).outerjoin(
            cashflow_subquery,
            (BankStatementSummary.month_date == cashflow_subquery.c.month_date) &
            (BankStatementSummary.account_name == cashflow_subquery.c.payment_method)
        )

        # 应用筛选条件到主查询
        if month_date:
            main_query = main_query.filter(BankStatementSummary.month_date == month_date)

        if account_name:
            main_query = main_query.filter(BankStatementSummary.account_name == account_name)

        return main_query.all()

