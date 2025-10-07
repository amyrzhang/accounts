# -*- coding: utf-8 -*-
# app/api/asset/resources.py
from datetime import datetime

from flask import request
from flask_restful import Resource

from app import db
from app.models import VCurrentAsset, AccountBalance, AccountMonthlyBalance
from app.utils.utils import format_percentage


class AccountBalanceResource(Resource):
    """账户余额资源"""

    def get(self):
        """获取账户余额信息"""
        result = AccountBalance.query.with_entities(
            AccountBalance.account_name,
            AccountBalance.account_type,
            AccountBalance.balance,
            AccountBalance.percent,
            AccountBalance.credit,
            AccountBalance.debit
        ).all()
        return [{
            'account_name': r.account_name,
            'account_type': r.account_type,
            'balance': r.balance,
            'percent': format_percentage(r.percent),
            'credit': r.credit,
            'debit': r.debit
        } for r in result], 200


class PositionListResource(Resource):
    """持仓列表资源"""

    def get(self):
        """
        查询当前持仓信息，支持分页和排序
        返回字段: 证券代码、持仓、现价、成本、持仓盈亏、持仓盈亏比、持仓成本、现值、仓位
        支持的查询参数:
        - pageNum: 页码，默认1
        - pageSize: 每页数量，默认10
        - sortBy: 排序字段
        - sortOrder: 排序顺序 (asc/desc)
        """
        try:
            # 获取分页参数
            page_num = int(request.args.get('pageNum', 1))
            page_size = int(request.args.get('pageSize', 10))

            # 构建查询
            query = VCurrentAsset.query

            # 应用排序
            sort_by = request.args.get('sortBy', 'stock_code')
            sort_order = request.args.get('sortOrder', 'asc')

            if hasattr(VCurrentAsset, sort_by):
                if sort_order.lower() == 'desc':
                    query = query.order_by(getattr(VCurrentAsset, sort_by).desc())
                else:
                    query = query.order_by(getattr(VCurrentAsset, sort_by).asc())
            else:
                query = query.order_by(VCurrentAsset.stock_code.asc())

            # 分页处理
            paginated_query = query.limit(page_size).offset((page_num - 1) * page_size).all()
            total_count = query.count()

            # 转换为字典列表
            positions_data = [position.to_dict() for position in paginated_query]

            # 计算总现值用于计算仓位
            # 注意：这里我们需要获取所有持仓的总现值，而不是当前页的
            all_positions = VCurrentAsset.query.all()
            total_realized_value = sum(position.realized_pnl for position in all_positions)

            # 添加仓位字段（现值/总现值）
            for position in positions_data:
                if total_realized_value > 0:
                    position['position_ratio'] = position['realized_pnl'] / float(total_realized_value)
                else:
                    position['position_ratio'] = 0

            return {
                "data": positions_data,
                "total": total_count,
                "total_realized_value": float(total_realized_value),
                "page_num": page_num,
                "page_size": page_size
            }, 200

        except Exception as e:
            return {"error": str(e)}, 500


from flask_restful import Resource


class AccountBalanceListResource(Resource):
    """账户月度余额列表资源"""

    def get(self):
        """获取所有账户余额记录"""
        balances = AccountMonthlyBalance.query.all()
        return [b.to_dict() for b in balances], 200

    def post(self):
        """添加新的账户余额记录"""
        data = request.get_json()
        try:
            new_balance = AccountMonthlyBalance(
                month_date=datetime.strptime(data['month_date'], '%Y-%m-%d').date(),
                account_name=data['account_name'],
                opening_balance=data['opening_balance'],
                closing_balance=data['closing_balance'],
                current_period_change=data['current_period_change'],
                data_source=data.get('data_source', ''),
                remark=data.get('remark', '')
            )
            db.session.add(new_balance)
            db.session.commit()
            return new_balance.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

#
# class AccountBalanceResource(Resource):
#     """单个账户余额资源"""
#
#     def get(self, id):
#         """根据ID获取单条账户余额记录"""
#         balance = AccountMonthlyBalance.query.get_or_404(id)
#         return balance.to_dict(), 200
#
#     def put(self, id):
#         """根据ID更新账户余额记录"""
#         balance = AccountMonthlyBalance.query.get_or_404(id)
#         data = request.get_json()
#         try:
#             if 'month_date' in data:
#                 balance.month_date = datetime.strptime(data['month_date'], '%Y-%m-%d').date()
#             if 'account_name' in data:
#                 balance.account_name = data['account_name']
#             if 'opening_balance' in data:
#                 balance.opening_balance = data['opening_balance']
#             if 'closing_balance' in data:
#                 balance.closing_balance = data['closing_balance']
#             if 'current_period_change' in data:
#                 balance.current_period_change = data['current_period_change']
#             if 'data_source' in data:
#                 balance.data_source = data['data_source']
#             if 'remark' in data:
#                 balance.remark = data['remark']
#             db.session.commit()
#             return balance.to_dict(), 200
#         except Exception as e:
#             db.session.rollback()
#             return {'error': str(e)}, 400
#
#     def delete(self, id):
#         """根据ID删除账户余额记录"""
#         balance = AccountMonthlyBalance.query.get_or_404(id)
#         try:
#             db.session.delete(balance)
#             db.session.commit()
#             return {'message': 'Record deleted successfully'}, 200
#         except Exception as e:
#             db.session.rollback()
#             return {'error': str(e)}, 400
