#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# version:     0.1
# update:      2.1  2021/12/29: 修复支付宝理财收支逻辑bug
# StartTime:   2024/8/5 20:224
# Finished:    2021/1/7 20:30
# Author:      AmyZhang

import pandas as pd
import os
from loader import WeixinTransactions, AlipayTransactions, Transactions, read_data_bank

if __name__ == '__main__':
    # 读取数据
    recorder = WeixinTransactions('data/微信支付账单(20240701-20240801).csv')
    data_weixin = recorder.load_data_weixin()
    recorder = AlipayTransactions('data/alipay_record_20240801_165204.csv')
    data_alipay = recorder.load_data_alipay()  # 读数据
    data_bank = read_data_bank('data/bank_record_20240701_20240731.csv')

    # 标记并修改数据
    es_df = Transactions(data_weixin, data_alipay, data_bank)
    es_df.check_bank_account(12316.84)
    # es_df.df.to_excel('merged_data.xlsx', index=False)

    # 增加 是否冲账数据 和 类别数据
    es_df.update_columns()
    print(es_df.balance, es_df.sums, es_df.category_sums)

    # es_df.write()  # 写入数据
