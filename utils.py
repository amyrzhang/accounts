# -*- coding: utf-8 -*-
__author__ = "Rui Zhang"
__email__ = "amyzhangrui@126.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = "Copyright 2024 Rui Zhang"
__status__ = "Development"
__description__ = "A simple web application to analyze bank transactions"

from datetime import datetime
from dateutil.relativedelta import relativedelta
import random
from shortuuid import uuid


def get_last_month():
    current_time = datetime.now()
    last_month = current_time - relativedelta(months=1)
    return last_month.strftime('%Y-%m')


def format_currency(number):
    return f"￥{number:,.2f}"


def format_percentage(number):
    return f"{number:.2f}%"


def generate_cashflow_id():
    """生成唯一 cashflow_id"""
    return uuid()


def process_transaction_data(data: dict) -> tuple:
    """
    处理交易数据核心逻辑（不包含数据库操作）

    入参：
    data = {
        "type": "BUY/SELL",
        "timestamp": "2023-08-01 10:00:00",
        "stock_code": "600519",
        "price": 1800.0,
        "quantity": 100,    # 与 amount 二选一
        "amount": 180000.0, # 与 quantity 二选一
        "fee": 5.0,         # 可选
        "payment_method": "券商名称" # 可选
    }

    出参：
    (processed_data, error_response)
    - 成功：返回包含计算结果的字典和 None
    - 失败：返回 None 和错误响应
    """
    try:
        # 参数校验
        required_fields = ['type', 'timestamp', 'stock_code', 'price']
        if missing := [field for field in required_fields if not data.get(field)]:
            return None, {"error": f"缺少必填字段: {', '.join(missing)}"}

        # 设置默认值
        fee = data.get('fee', 0.0)
        payment_method = data.get('payment_method') or '东方财富证券(5700)'

        # 计算交易类型参数
        transaction_type = data['type']
        debit_credit = '支出' if transaction_type == 'BUY' else '收入'
        cashflow_type = '申购' if transaction_type == 'BUY' else '赎回'

        # 金额计算逻辑
        if data.get('amount'):
            quantity = round((data['amount'] - (fee if transaction_type == 'BUY' else -fee)) / data['price'], 2)
            amount = data['amount']
        elif data.get('quantity'):
            quantity = data['quantity']
            amount = round(data['price'] * quantity + (fee if transaction_type == 'BUY' else -fee), 2)
        else:
            return None, {"error": "必须提供 quantity 或 amount"}

        return {
            'payment_method': payment_method,
            'debit_credit': debit_credit,
            'cashflow_type': cashflow_type,
            'quantity': quantity,
            'amount': amount,
            'fee': fee
        }, None

    except ZeroDivisionError:
        return None, {"error": "价格不能为0"}
    except ValueError as e:
        return None, {"error": f"数值计算错误: {str(e)}"}
    except Exception as e:
        return None, {"error": f"数据处理失败: {str(e)}"}