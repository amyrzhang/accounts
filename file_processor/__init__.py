# -*- coding: utf-8 -*-
"""
Processor模块初始化文件
"""

from .base import Processor
from .weixin import WeixinProcessor
from .alipay import AlipayProcessor

__all__ = ['Processor', 'WeixinProcessor', 'AlipayProcessor']
