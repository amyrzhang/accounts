# -*- coding: utf-8 -*-
__author__ = "Rui Zhang"
__email__ = "amyzhangrui@126.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = "Copyright 2024 Rui Zhang"
__status__ = "Development"
__description__ = "A simple web application to analyze bank transactions"


def format_currency(number):
    return f"￥{number:,.2f}"


def format_percentage(number):
    return f"{number * 100:.2f}%"
