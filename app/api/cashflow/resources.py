# -*- coding: utf-8 -*-
# app/api/cashflow/resources.py
import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from shortuuid import uuid
from sqlalchemy import func, desc

import app
from app.models.cashflow import Cashflow
from app.extentions import db
from app.services.import_service import ImportService
from app.utils.utils import generate_cashflow_id


class CashflowListResource(Resource):
    """现金流列表资源"""

    def get(self):
        """根据 cashflow_id 查询所有记录并支持分页"""
        # 获取分页参数
        page_num = int(request.args.get('pageNum', 1))
        page_size = int(request.args.get('pageSize', 10))

        # 构建查询
        query = Cashflow.query

        # 应用过滤条件
        if request.args:
            for param, value in request.args.items():
                if hasattr(Cashflow, param):
                    if param == 'time':
                        query = query.filter(func.date_format(Cashflow.time, '%Y-%m') == value)
                    else:
                        query = query.filter(getattr(Cashflow, param) == value)

        # 分页处理
        paginated_query = query.order_by(desc(Cashflow.time)).limit(page_size).offset((page_num - 1) * page_size).all()
        return {"data": [cashflow.to_dict() for cashflow in paginated_query], "total": query.count()}, 200

    def post(self):
        """添加一条记录"""
        data = request.get_json()
        cashflows = add_cashflow_records(data)
        return {
            "cashflow_id": [t.cashflow_id for t in cashflows],
            "message": "Cashflow created successfully"
        }, 201


class CashflowResource(Resource):
    """现金流资源"""
    def get(self, cashflow_id):
        """查询一条记录"""
        transaction = Cashflow.query.get_or_404(cashflow_id)
        return transaction.to_dict()

    def put(self, cashflow_id):
        """修改一条记录"""
        data = request.get_json()
        cashflow = Cashflow.query.get_or_404(cashflow_id)

        # 遍历键值对并更新字段
        for key, value in data.items():
            if hasattr(cashflow, key):
                setattr(cashflow, key, value)

        db.session.commit()
        return cashflow.to_dict()

    def delete(self, cashflow_id):
        """根据 cashflow_id 删除所有相关记录"""
        try:
            # 查询所有 cashflow_id 匹配的记录
            cashflows = Cashflow.query.filter_by(cashflow_id=cashflow_id).all()

            if not cashflows:
                return {"error": "No records found with the given cashflow_id"}, 404

            # 删除所有匹配的记录
            for cashflow in cashflows:
                db.session.delete(cashflow)

            # 提交事务
            db.session.commit()
            return {'msg': f'{cashflow_id} deleted successfully'}, 204
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

def add_cashflow_records(data_list):
    """
    批量添加现金流记录到数据库

    该函数会检查每条记录是否已存在，如果不存在则创建新的现金流记录。
    记录的唯一性通过时间（精确到分钟）、借贷方向、金额和支付方式来判断。

    Args:
        data_list (list): 包含现金流数据的字典列表，每个字典应包含以下键：
            - time (str or datetime): 交易时间
            - debit_credit (str): 借贷方向，'收入' 或 '支出'
            - amount (float): 金额
            - payment_method (str): 支付方式
            - type (str, optional): 交易类型
            - counterparty (str, optional): 交易对手
            - goods (str, optional): 商品或服务描述
            - status (str, optional): 状态
            - category (str, optional): 分类
            - source (str, optional): 数据来源

    Returns:
        list: 新创建的 Cashflow 对象列表

    Note:
        - 如果记录已存在（根据时间、借贷方向、金额和支付方式匹配），则不会重复创建
        - 所有新创建的记录会在一个数据库事务中提交
    """
    created_cashflow = []

    for data in data_list:
        time = datetime.strptime(data.get('time'), '%Y-%m-%d %H:%M:%S') if isinstance(data.get('time'),
                                                                                      str) else data.get('time')
        debit_credit = data.get('debit_credit')
        amount = data.get('amount')
        payment_method = data.get('payment_method')

        # 查询是否存在相同记录
        existing_cashflow = Cashflow.query.filter(
            func.date_format(Cashflow.time, '%Y-%m-%d %H:%i') == time.strftime('%Y-%m-%d %H:%M'),
            Cashflow.debit_credit == debit_credit,
            Cashflow.amount == amount,
            Cashflow.payment_method == payment_method
        ).first()

        if not existing_cashflow:
            cashflow = Cashflow(
                cashflow_id=generate_cashflow_id(),
                time=time,
                type=data.get('type'),
                counterparty=data.get('counterparty'),
                goods=data.get('goods'),
                debit_credit=debit_credit,
                amount=amount,
                payment_method=payment_method,
                status=data.get('status'),
                category=data.get('category'),
                source=data.get('source'),
            )
            db.session.add(cashflow)
            created_cashflow.append(cashflow)

    db.session.commit()
    return created_cashflow


from flask_restful import Resource


class TransferResource(Resource):
    """转账资源"""

    def post(self):
        """创建转账记录"""
        data = request.get_json()
        time = data.get('time')
        from_account = data['payment_method']
        to_account = data['counterparty']
        amount = data['amount']
        type, goods = '自转账', '转账'

        # 生成唯一 cashflow_id
        cashflow_id_out = generate_cashflow_id()
        cashflow_id_in = generate_cashflow_id()
        transfer_id = uuid.uuid4().hex

        try:
            # 开启事务
            with db.session.begin():
                # 创建流出记录
                out_record = Cashflow(
                    cashflow_id=cashflow_id_out,
                    transfer_id=transfer_id,
                    time=time,
                    payment_method=from_account,
                    counterparty=to_account,
                    debit_credit='支出',
                    amount=amount,
                    type=type,
                    goods=goods
                )
                db.session.add(out_record)

                # 创建流入记录
                in_record = Cashflow(
                    cashflow_id=cashflow_id_in,
                    transfer_id=transfer_id,
                    time=time,
                    payment_method=to_account,
                    counterparty=from_account,
                    debit_credit='收入',
                    amount=amount,
                    type=type,
                    goods=goods
                )
                db.session.add(in_record)

            return {
                "cashflow_id_out": cashflow_id_out,
                "cashflow_id_in": cashflow_id_in,
                "transfer_id": transfer_id,
                "message": "Cashflow created successfully"
            }, 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def get(self, transfer_id):
        """根据转账ID查询转账记录"""
        records = Cashflow.query.filter(Cashflow.transfer_id == transfer_id).all()

        if not records:
            return {"error": "Cashflow not found"}, 404

        result = [rcd.to_dict() for rcd in records]
        return result, 200

    def delete(self, transfer_id):
        """根据转账ID删除转账记录"""
        try:
            # 查询所有 transfer_id 匹配的记录
            records = Cashflow.query.filter(Cashflow.transfer_id == transfer_id).all()

            if not records:
                return {"error": "Cashflow not found"}, 404

            # 删除所有匹配的记录
            for record in records:
                db.session.delete(record)
            db.session.commit()

            return {"message": f"Successfully deleted {len(records)} records"}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


class UploadResource(Resource):
    """文件上传资源"""

    def post(self):
        """上传并处理文件"""
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return {"error": "No file part"}, 400
        file = request.files['file']

        # 检查是否选择了文件
        if file.filename == '':
            return {"error": "No selected file"}, 400
        if file:
            file_name = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

            if os.path.exists(file_path):
                return {"error": f"File already exists: {file_name}"}, 409

            try:
                file.save(file_path)
                data = ImportService.import_cashflow(file_path)
                add_cashflow_records(data)
            except Exception as e:
                os.remove(file_path)
                return {"error": f"Error processing file: {str(e)}"}, 500

            return {"message": f"File saved successfully as {file_name}"}, 200
        return {"error": f"Invalid file as {file}"}, 400
