# -*- coding: utf-8 -*-
# app/api/transaction/resources.py
from datetime import datetime

from flask import request
from flask_restful import Resource
from sqlalchemy import desc

from app.extentions import db
from app.models.cashflow import Cashflow
from app.models.transaction import Transaction
from app.utils.utils import determine_cashflow_properties, generate_cashflow_id


class TransactionListResource(Resource):
    def get(self):
        """获取交易记录列表，支持分页和过滤"""
        # 获取分页参数
        page_num = int(request.args.get('pageNum', 1))
        page_size = int(request.args.get('pageSize', 10))

        # 构建查询
        query = Transaction.query

        # 应用过滤条件
        if request.args:
            for param, value in request.args.items():
                if hasattr(Transaction, param) and param not in ['pageNum', 'pageSize', 'dateRange',
                                                                       'stock_code']:
                    query = query.filter(getattr(Transaction, param) == value)

            # 处理时间范围参数
            start_date, end_date = request.args.get('startDate'), request.args.get('endDate')
            if start_date and end_date:
                try:
                    date_begin = datetime.strptime(start_date, '%Y-%m-%d')
                    date_end = datetime.strptime(end_date, '%Y-%m-%d')
                    query = query.filter(Transaction.timestamp.between(date_begin, date_end))
                except ValueError:
                    pass  # 如果日期格式不正确，忽略该过滤条件

            # 处理证券代码参数
            stock_code = request.args.get('stock_code')
            if stock_code:
                query = query.filter(Transaction.stock_code.like(f'%{stock_code}%'))

        # 分页处理
        paginated_query = query.order_by(desc(Transaction.timestamp)).limit(page_size).offset(
            (page_num - 1) * page_size).all()
        return {"data": [transaction.to_dict() for transaction in paginated_query], "total": query.count()}, 200

    def post(self):
        """
        创建交易记录（保持原有数据库操作）
        请求参数：
        [
            {
                "stock_code": "股票代码，如 000001",
                "type": "交易类型，BUY 或 SELL",
                "timestamp": "交易时间，格式为 YYYY-MM-DD HH:MM:SS",
                "price": "交易价格，数值类型",
                "fee": "手续费，数值类型"
                "amount": "金额，数值类型"
            }
        ]
        """
        data_list = request.get_json()
        created_ids = []
        errors = []

        for data in data_list:
            # 处理交易数据，计算数量、金额等字段
            cashflow_properties, error_response = determine_cashflow_properties(data)

            # 如果处理过程中出现错误，则记录错误信息并跳过当前记录
            if error_response:
                errors.append(error_response)
                continue

            try:
                # 开启数据库事务，确保数据一致性
                with db.session.begin():
                    # 创建 Transaction 表记录
                    transaction = Transaction(
                        stock_code=data['stock_code'],
                        type=data['type'],
                        timestamp=data['timestamp'],
                        quantity=data['quantity'],
                        price=data['price'],
                        fee=data['fee'],
                        amount=data['amount']
                    )
                    db.session.add(transaction)
                    db.session.flush()  # 刷新会话以生成 transaction_id

                    # 创建 Cashflow 表记录并与 Transaction 表关联
                    cashflow_record = Cashflow(
                        cashflow_id=generate_cashflow_id(),
                        transaction_id=transaction.transaction_id,
                        type=cashflow_properties['cashflow_type'],
                        category="投资理财",
                        time=data['timestamp'],
                        payment_method=data['payment_method'],
                        counterparty=data['stock_code'],
                        debit_credit=cashflow_properties['debit_credit'],
                        amount=data['amount'] + data['fee'],
                        goods=f'股票代码:{data["stock_code"]},金额:{data["amount"]},价格:{data["price"]},数量:{data["quantity"]},费用:{data["fee"]}'
                    )
                    db.session.add(cashflow_record)
                    # 记录成功创建的 transaction_id
                    created_ids.append(transaction.transaction_id)

            except Exception as e:
                # 出现异常时回滚事务并返回错误信息
                db.session.rollback()
                return {"error": str(e)}, 500

        # 如果存在处理失败的记录，则返回部分成功信息和错误详情
        if errors:
            return {
                "message": f"部分记录处理失败，成功创建 {len(created_ids)} 条",
                "errors": errors,
                "created_ids": created_ids
            }, 207

        # 所有记录都成功创建时返回成功信息
        return {"message": "Transaction created successfully", "transaction_id": created_ids}, 201


class TransactionResource(Resource):
    """单个交易记录资源"""

    def get(self, transaction_id):
        """根据ID获取单个交易记录"""
        records = model.Transaction.query.filter_by(
            transaction_id=transaction_id
        ).all()

        if not records:
            return {"error": "Transaction not found"}, 404

        result = [rcd.to_dict() for rcd in records]
        return result, 200

    def put(self, transaction_id):
        """更新交易记录并级联更新现金流"""
        data = request.get_json()

        try:
            # 1. 获取原始交易记录
            transaction = Transaction.query.get_or_404(transaction_id)

            # 2. 获取关联的现金流记录
            cashflow = Cashflow.query.filter_by(transaction_id=transaction_id).first()
            if not cashflow:
                return {"error": "关联的现金流记录不存在"}, 404

            # 3. 更新交易表字段
            update_fields = []
            stock_code = data.get('stock_code', transaction.stock_code)
            timestamp = data.get('timestamp', transaction.timestamp)
            type = data.get('type', transaction.type)
            price = data.get('price', transaction.price)
            quantity = data.get('quantity', transaction.quantity)
            amount = data.get('amount', transaction.amount)
            fee = data.get('fee', transaction.fee)

            # 更新交易记录
            transaction.stock_code = stock_code
            transaction.timestamp = timestamp
            transaction.type = type
            transaction.price = price
            transaction.quantity = quantity
            transaction.amount = amount
            transaction.fee = fee

            update_fields.extend(['quantity', 'price'])

            # 更新现金流记录
            cashflow.time = timestamp
            cashflow.counterparty = stock_code
            cashflow.amount = amount
            cashflow.goods = f'股票代码:{data["stock_code"]},金额:{data["amount"]},价格:{data["price"]},数量:{data["quantity"]},费用:{data["fee"]}'
            update_fields.extend(['amount', 'goods'])

            # 4. 提交修改
            db.session.commit()

            return {
                "message": "更新成功",
                "updated_fields": update_fields,
                "transaction": transaction.to_dict(),
                "cashflow": cashflow.to_dict()
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, transaction_id):
        """删除交易记录及其关联的现金流记录"""
        try:
            # 查询同一交易的 transaction 记录和 cashflow 记录
            transaction_record = Transaction.query.filter_by(
                transaction_id=transaction_id
            ).first()
            cashflow_record = Cashflow.query.filter_by(
                transaction_id=transaction_id
            ).first()

            if not transaction_record or not cashflow_record:
                return {"error": "Transaction not found"}, 404

            # 删除记录
            db.session.delete(transaction_record)
            db.session.delete(cashflow_record)

            # 提交事务
            db.session.commit()
            return {"message": "Transaction deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500