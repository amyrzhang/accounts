#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# version:     0.1
# update:      2.1  2021/12/29: 修复支付宝理财收支逻辑bug
# StartTime:   2024/8/5 20:224
# Finished:    2021/1/7 20:30
# Author:      AmyZhang

import pandas as pd
import os
from uploader import WeixinProcessor, AlipayProcessor, Processor, read_data_bank
from calculate import Analyzer
from app import get_transactions
from flask import jsonify

if __name__ == '__main__':
    a = Analyzer()
    b = a.account_sums
    res =  {
        'expenditure': -a.sums['支出'],
        'income': a.sums['收入'],
        'balance': a.sums.sum()
    }
    # 读取数据
    recorder = WeixinProcessor('uploads/微信支付账单(20240801-20240831).csv')
    data_weixin = recorder.df
    recorder = AlipayProcessor('uploads/alipay_record_20240914_090323.csv')
    a = recorder.df
