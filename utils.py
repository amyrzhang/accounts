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