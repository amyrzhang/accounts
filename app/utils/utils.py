# -*- coding: utf-8 -*-
# app/utils/utils.py
__author__ = "Rui Zhang"
__email__ = "amyzhangrui@126.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = "Copyright 2024 Rui Zhang"
__status__ = "Development"
__description__ = "A simple web application to analyze bank transactions"

import decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from shortuuid import uuid

def get_last_month():
    current_time = datetime.now()
    last_month = current_time - relativedelta(months=1)
    return last_month.strftime('%Y-%m')


def format_currency(number):
    return f"{number:,.2f}"


def format_percentage(number):
    return f"{number:.2f}%"


def generate_cashflow_id():
    """生成唯一 cashflow_id"""
    return uuid()


def calculate_amount_quantity(data: dict, price: float, adjusted_fee: float) -> tuple:
    if data.get('amount'):
        amount = round(data['amount'], 2)
        quantity = round((amount - adjusted_fee) / price, 2)
    elif data.get('quantity'):
        quantity = round(data['quantity'], 2)
        amount = round(price * quantity + adjusted_fee, 2)
    else:
        return None, None
    return amount, quantity


def determine_cashflow_properties(data: dict) -> tuple:
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
        # 计算交易类型参数
        if data['type'] == 'BUY':
            debit_credit, cashflow_type = '支出', '申购'
        elif data['type'] == 'SELL':
            debit_credit, cashflow_type = '收入', '赎回'
        elif data['type'] == 'DIVIDEND':
            debit_credit, cashflow_type = '收入', '红利'
        else:
            return None, {"error": "Invalid transaction type"}

        return {
            'debit_credit': debit_credit,
            'cashflow_type': cashflow_type
        }, None

    except ZeroDivisionError:
        return None, {"error": "价格不能为0"}
    except ValueError as e:
        return None, {"error": f"数值计算错误: {str(e)}"}
    except Exception as e:
        return None, {"error": f"数据处理失败: {str(e)}"}


def calculate_cashflow_amount(
        transaction_type: str,
        amount: float | decimal.Decimal,
        fee: float | decimal.Decimal,
) -> float:
    """
    根据交易类型计算现金流金额。

    Args:
        transaction_type (str): 交易类型 ('BUY' 或 'SELL')。
        amount (float | decimal.Decimal): 交易金额。
        fee (float | decimal.Decimal): 手续费。

    Returns:
        float: 计算后的现金流金额。
    """
    if transaction_type.upper() == 'BUY':
        return float(amount) + float(fee)
    elif transaction_type.upper() == 'SELL':
        return float(amount) - float(fee)
    else:
        # 处理其他类型，比如dividend
        return float(amount)
