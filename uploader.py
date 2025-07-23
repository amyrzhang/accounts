#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import re
import pandas as pd
import os
import json
import chardet

import logging


def load_to_df(filepath):
    try:
        if '微信支付账单' in filepath:
            wp = WeixinProcessor(filepath)
            return wp.df.to_dict(orient='records')
        if 'alipay_record' in filepath or '支付宝' in filepath:
            ap = AlipayProcessor(filepath)
            return ap.df.to_dict(orient='records')
        return f'Unsupported file type: {filepath}', 400
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {str(e)}", exc_info=True)
        return f'Error processing file: {filepath}', 500


class Processor:
    def __init__(self, path):
        self.path = path
        self._df = pd.DataFrame()

    @property
    def balance(self):
        if 'alipay' in self.path:
            file_encoding = 'gbk'
        else:
            file_encoding = self.file_encoding
        with open(self.path, 'r', encoding=file_encoding) as f:
            text = f.read()
            # 定义正则表达式
            income_pattern = r'收入：\d+笔\s+(\d+\.\d+)元'
            expense_pattern = r'支出：\d+笔\s+(\d+\.\d+)元'
            # 搜索并提取收入和支出金额
            income_match = re.search(income_pattern, text)
            if income_match:
                incomes = float(income_match.group(1))
            expense_match = re.search(expense_pattern, text)
            if expense_match:
                expenditures = float(expense_match.group(1))
        return round(incomes - expenditures, 2)

    @property
    def file_encoding(self):
        """
        微信对账单的编码方式：utf-8
        支付宝对账单的编码方式：gbk
        """
        if '微信' in self.path:
            return 'utf-8'
        return 'gbk'

    @property
    def df(self):
        return self._df

    def check_balance(self, df):
        if df.empty:
            return
        sums = df.groupby(['debit_credit'])['amount'].sum()
        if '收入' not in sums: sums['收入'] = 0

        balance = round(sums['收入'] - sums['支出'], 2)
        if balance == self.balance:
            return f'{self.path} is checked'


    @property
    def data_source(self):
        if '微信' in self.path:
            return '微信'
        return '支付宝'

    @staticmethod
    def process_category_row(row):
        """识别交易类别"""
        text = str(row['交易对方']) + ' ' + str(row['商品'])
        shopping_pattern = '平台商户|抖音电商商家|快递'  # 根据交易对方判断
        transportation_pattern = '出行|加油|停车|中铁|12306'  # 根据二者判断
        telecommunication_pattern = '联通'  # 根据交易对方判断
        salary_pattern = '工资'
        if re.search(shopping_pattern, text):
            return '购物'
        elif re.search(transportation_pattern, text):
            return '交通'
        elif re.search(telecommunication_pattern, text):
            return '通讯'
        elif re.search(salary_pattern, text):
            return '工资'
        else:
            return '餐饮'




class WeixinProcessor(Processor):
    @property
    def balance(self):
        return super().balance

    @property
    def df(self):
        df = pd.read_csv(
            self.path, header=16, usecols=[0, 1, 2, 3, 4, 5, 6, 7],
            skipfooter=0,
            encoding=self.file_encoding
        )  # 数据获取，微信

        df = self.strip_in_data(df)  # 去除列名与数值中的空格。
        df['交易时间'] = pd.to_datetime(df['交易时间'])  # 数据类型更改
        df['金额(元)'] = df['金额(元)'].astype('float64')  # 数据类型更改

        df = df.apply(self.clean_weixin_payment_method, axis='columns')
        df['category'] = df.apply(self.process_category_row, axis='columns')
        df['source'] = self.data_source

        df.rename(columns={
            '交易时间': 'time',
            '来源': 'source',
            '收/支': 'debit_credit',
            '当前状态': 'status',
            '交易类型': 'type',
            '交易对方': 'counterparty',
            '商品': 'goods',
            '金额(元)': 'amount',
            '支付方式': 'payment_method'
        }, inplace=True)
        if self.check_balance(df): return df

    @staticmethod
    def strip_in_data(data):
        """"去掉金额的货币符号"""
        data = data.rename(columns={column_name: column_name.strip() for column_name in data.columns})
        return data.map(lambda x: x.strip().strip('¥') if isinstance(x, str) else x)

    @staticmethod
    def clean_weixin_payment_method(row):
        """微信收入的交易账户为 零钱 """
        if row['收/支'] == '收入' and row['支付方式'] == '/' and row['当前状态'] == "已存入零钱":
            row['支付方式'] = '零钱'
        return row



class AlipayProcessor(Processor):
    def __init__(self, path):
        super().__init__(path)

    @property
    def balance(self):
        return super().balance

    @property
    def df(self):  # 获取支付宝数据
        df = pd.read_csv(
            self.path, header=22, usecols=[0, 2, 4, 5, 6, 7, 8],
            encoding=self.file_encoding
        )
        df['交易时间'] = pd.to_datetime(df['交易时间'])  # 数据类型更改
        df['金额'] = df['金额'].astype('float64')  # 数据类型更改

        # 处理 NaN 值
        df['交易对方'].fillna('', inplace=True)

        # 多账户合并付款，以 & 分隔，需手工整理
        df = df.apply(self.clean_alipay_payment_method, axis='columns')

        # 过滤有退款的交易，条件是：支付状态=交易成功 & 收/支=不计收支
        df = df[(df['交易状态'].isin(['交易成功', '支付成功'])) &\
                (df['收/支'].isin(['收入', '支出']))]

        # 增加字段：类型 type，类别 category、来源 source
        df.insert(1, 'type', "商户消费")
        df.rename(columns={'商品说明': '商品'}, inplace=True)
        df["category"] = df.apply(self.process_category_row, axis='columns')
        df["source"] = self.data_source

        df.rename(columns={
            '交易时间': 'time',
            '交易对方': 'counterparty',
            '商品': 'goods',
            '收/支': 'debit_credit',
            '金额': 'amount',
            '收/付款方式': 'payment_method',
            '交易状态': 'status',
        }, inplace=True)  # 修改列名称
        if self.check_balance(df):  return df

    @staticmethod
    def clean_alipay_payment_method(row):
        """
        多账户合并付款，以 & 分隔，需手工整理
        去掉支付宝的支付方式后缀，整理格式例如：'光大银行信用卡(5851)'
        :return: str
        """
        if row['收/支'] == '收入' and pd.isnull(row['收/付款方式']):
            row['收/付款方式'] = '余额宝'
        row['收/付款方式'] = str(row['收/付款方式'])[:13]
        return row

def process_excluded_row(row):
    """
    处理有退款交易，将当前状态为已全额退款或已退款的交易，增加枚举值：不计收支
    添加金额的正负号

    微信中性交易：充值/提现/理财通购买/零钱通存取/信用卡还款等交易，将计入中性交易
    支付宝不计收支：充值提现、账户转存或者个人设置收支等不计入为收入或者支出，记为不计收支类；

    微信枚举值：'已全额退款', '已退款', '退款成功', '提现已到账', '还款成功'
    支付宝枚举值：'交易关闭'
    :param row: pa.DataFrame
    :return:
    """
    status = row['支付状态']
    amount = row['金额']
    match = re.search(r"(已退款)[(]?￥(\d+\.\d+)[)]?", status)

    if match:  # 如果部分退款
        amount -= float(match.group(2))
    elif status in ('已全额退款', '对方已退还'):  # 如果全额退款
        if amount != 11:  # TODO: 开发自动成对冲账功能
            row['收/支'] = '不计收支'
            amount = 0

    row['amount'] = amount if row['收/支'] == '收入' else -amount  # 考虑收支添加符号
    return row





def settle_transactions(data):
    """
    更新 'amount' 列的数据，其中 '是否冲账' 列为 1 的行将被修改。

    参数:
    - uploads: pd.DataFrame, 包含 '是否冲账' 和 '收/支' 列的数据框
    """
    remaining_amount = data.loc[data['是否冲账'] == 1, 'amount'].sum()

    if remaining_amount >= 0:
        index = data.loc[(data['是否冲账'] == 1) & (data['收/支'] == '收入')].index[0]
    else:
        index = data.loc[(data['是否冲账'] == 1) & (data['收/支'] == '支出')].index[0]

    # 将 '是否冲账' 为 1 的行的 'amount' 列设为 0
    data.loc[data['是否冲账'] == 1, 'amount'] = 0
    # 将选定的行的 'amount' 列设为 remaining_amount
    data.at[index, 'amount'] = remaining_amount
    return data

if __name__ == '__main__':
    filepath="支付宝交易明细(20250401-20250430).csv"
    res = load_to_df(filepath)