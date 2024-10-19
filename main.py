#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# version:     0.1
# update:      2.1  2021/12/29: 修复支付宝理财收支逻辑bug
# StartTime:   2024/8/5 20:224
# Finished:    2021/1/7 20:30
# Author:      AmyZhang


from uploader import WeixinProcessor, AlipayProcessor, Processor
from query import Analyzer

if __name__ == '__main__':
    # a = Analyzer()
    # a.filter({'month': '2024-08'})
    # res =  {
    #     'expenditure': -a.sums['支出'],
    #     'income': a.sums['收入'],
    #     'balance': a.sums.sum()
    # }
    # 读取数据
    recorder = WeixinProcessor('uploads/微信支付账单(20240901-20240930).csv')
    data_weixin = recorder.df
    recorder = AlipayProcessor('uploads/alipay_record_20240914_090323.csv')
    a = recorder.df
