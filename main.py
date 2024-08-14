#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# version:     0.1
# update:      2.1  2021/12/29: 修复支付宝理财收支逻辑bug
# StartTime:   2024/8/5 20:224
# Finished:    2021/1/7 20:30
# Author:      AmyZhang

import pandas as pd
import tkinter.filedialog
import msvcrt
import os
from loader import WeixinTransactions, AlipayTransactions, Transactions, read_data_bank


def frontend():
    # 路径设置
    print('提示：请在弹窗中选择要导入的【微信】账单文件\n')
    path_wx = tkinter.filedialog.askopenfilename(title='选择要导入的微信账单：',
                                                 filetypes=[('所有文件', '.*'), ('csv文件', '.csv')])
    if path_wx == '':  # 判断是否只导入了微信或支付宝账单中的一个
        cancel_wx = 1
    else:
        cancel_wx = 0

    print('提示：请在弹窗中选择要导入的【支付宝】账单文件\n')
    path_zfb = tkinter.filedialog.askopenfilename(title='选择要导入的支付宝账单：',
                                                  filetypes=[('所有文件', '.*'), ('csv文件', '.csv')])
    if path_zfb == '':  # 判断是否只导入了微信或支付宝账单中的一个
        cancel_zfb = 1
    else:
        cancel_zfb = 0

    while cancel_zfb == 1 and cancel_wx == 1:
        print('\n您没有选择任何一个账单！     请按任意键退出程序')
        ord(msvcrt.getch())

    path_account = tkinter.filedialog.askopenfilename(title='选择要导出的目标账本表格：',
                                                      filetypes=[('所有文件', '.*'), ('Excel表格', '.xlsx')])
    while path_account == '':  # 判断是否选择了账本
        print('\n年轻人，不选账本怎么记账？      请按任意键退出程序')
        ord(msvcrt.getch())

    path_write = path_account

    # 判断是否只导入了微信或支付宝账单中的一个
    if cancel_wx == 1:
        data_wx = pd.DataFrame()
    else:
        # data_wx = read_data_wx(path_wx)  # 读数据
        pass
    if cancel_zfb == 1:
        data_zfb = pd.DataFrame()
    else:
        # data_zfb = read_data_zfb(path_zfb)  # 读数据
        pass
    return data_wx, data_zfb, path_write


if __name__ == '__main__':
    # 读取数据
    recorder = WeixinTransactions('data/微信支付账单(20240701-20240801).csv')
    data_weixin = recorder.load_data_weixin()
    recorder = AlipayTransactions('data/alipay_record_20240801_165204.csv')
    data_alipay = recorder.load_data_alipay()  # 读数据
    data_bank = read_data_bank('data/bank_record.csv')

    # 标记并修改数据
    es_df = Transactions(data_weixin, data_alipay, data_bank)
    es_df.check_bank_account(12316.84)
    if not os.path.exists('data/merged_data.xlsx'):
        es_df.df.to_excel('data/merged_data.xlsx', index=False)

    # 增加 是否冲账数据 和 类别数据
    col_values = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
    ]
    category_values = [
        '餐饮',
        '餐饮',
        '餐饮',
        '交通',
        '餐饮',
        '餐饮',
        '购物',
        '餐饮',
        '餐饮',
        '餐饮',
        '购物',
        '购物',
        '购物',
        '餐饮',
        '购物',
        '购物',
        '购物',
        '购物',
        '购物_电子烟',
        '休闲娱乐',
        '购物',
        '购物',
        '工资',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '购物',
        '购物',
        '餐饮',
        '购物',
        '餐饮',
        '餐饮',
        '餐饮',
        '交通',
        '交通',
        '购物',
        '交通',
        '二手交易',
        '交通',
        '餐饮',
        '通讯',
        '购物',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '购物',
        '通讯',
        '购物',
        '餐饮',
        '餐饮',
        '餐饮',
        '餐饮',
        '通讯',
        '交通',
        '购物',
        '购物',
        '餐饮',
        '购物',
        '餐饮',
        '餐饮',
        '购物',
        '工资'
    ]
    col1 = {'是否冲账': col_values, 'category': category_values}
    es_df.update_columns(col1)
    print(es_df.balance, es_df.sums, es_df.category_sums)

    es_df.write()  # 写入数据

