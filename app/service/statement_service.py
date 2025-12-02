# -*- coding: utf-8 -*-
# app/service/statement_service.py
from app.extentions import db
from app.models import AccountMonthlyBalance, MonthlyBalance
from app.models import Cashflow
from sqlalchemy import func


class StatementService:
    @staticmethod
    def get_monthly_report(account_id, year_month):
        """
        获取指定账户、指定月份的完整报表（含计算字段）
        :param account_id: 账户ID
        :param year_month: 年月（如：202509）
        :return: 完整报表数据（字典格式）
        """
        # 1. 获取银行账单基础数据（期初/期末/当期变动）
        statement = AccountMonthlyBalance.query.filter_by(
            account_id=account_id,
            year_month=year_month
        ).first()
        if not statement:
            raise ValueError(f"未找到账户{account_id}在{year_month}的银行账单")

        # 2. 计算流水的“本期总收入”和“本期总支出”
        # 时间范围：当月1日00:00:00 到 当月最后1日23:59:59
        start_date = f"{year_month[:4]}-{year_month[4:]}-01 00:00:00"
        end_date = f"{year_month[:4]}-{year_month[4:]}-31 23:59:59"

        # 总收入：sum(amount where amount>0)
        total_income = db.session.query(func.sum(Cashflow.amount)).filter(
            Cashflow.account_id == account_id,
            Cashflow.tx_time.between(start_date, end_date),
            Cashflow.amount > 0
        ).scalar() or 0.00

        # 总支出：sum(abs(amount) where amount<0)
        total_expense = db.session.query(func.sum(func.abs(Cashflow.amount))).filter(
            Cashflow.account_id == account_id,
            Cashflow.tx_time.between(start_date, end_date),
            Cashflow.amount < 0
        ).scalar() or 0.00

        # 3. 计算“期末账面余额”和“差额”
        closing_book_balance = round(
            float(statement.opening_balance) + float(total_income) - float(total_expense),
            2
        )
        difference = round(
            float(statement.closing_balance) - closing_book_balance,
            2
        )

        # 4. 获取最新的调整说明（取最近一条）
        adjustment = statement.adjustments[-1] if statement.adjustments else None
        adjust_note = adjustment.adjust_note if adjustment else ""

        # 5. 组装最终报表数据
        return {
            "month": f"{year_month[:4]}-{year_month[4:]}",  # 格式：2025-09
            "account_name": statement.account.account_name,
            "opening_balance": float(statement.opening_balance),
            "closing_balance": float(statement.closing_balance),
            "period_change": float(statement.period_change),
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "closing_book_balance": closing_book_balance,
            "difference": difference,
            "adjust_note": adjust_note,
            "statement_id": statement.id  # 用于后续调整说明关联
        }

    @staticmethod
    def _get_monthly_balance_data(filter_month_date):
        """Get monthly balance data using the same logic as MonthlyBalanceResource"""
        query = MonthlyBalance.query
        # Apply the same filtering logic as in MonthlyBalanceResource
        if filter_month_date:
            query = query.filter(MonthlyBalance.month == filter_month_date[:7])

        records = query.all()

        # Convert to dict format (same as MonthlyBalanceResource)
        return records[0].balance