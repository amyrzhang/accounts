#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import re
import pandas as pd
import os
import json
import chardet



def load_to_df(filepath):
    if '微信支付账单' in filepath:
        wp = WeixinProcessor(filepath)
        data = wp.read_data()#.df  # 写入数据
    elif 'alipay_record' in filepath:
        data = AlipayProcessor(filepath).df  # 写入数据
        data.rename(columns={
            '交易时间': 'time',
            '来源': 'source',
            '收/支': 'expenditure_income',
            '支付状态': 'status',
            '类型': 'type',
            'category': 'category',
            '交易对方': 'counterparty',
            '商品': 'goods',
            '是否冲账': 'reversed',
            '金额': 'amount',
            '支付方式': 'pay_method'
        }, inplace=True)
    else:
        return f'Unsupported file type', 400

    return data


class Processor:
    def __init__(self, path):
        self.path = path

    @property
    def balance(self):
        if 'alipay' in self.path:
            file_encoding = 'gbk'
        else:
            file_encoding = self.encoding
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
    def encoding(self):
        """支付宝对账单的编码方式：GB2312，微信对账单的编码方式：UTF-8"""
        with open(self.path, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            return result['encoding']

    @property
    def data_source(self):
        if '微信' in self.path:
            return '微信'
        elif 'alipay' in self.path:
            return '支付宝'
        else:
            return '手工'

    @staticmethod
    def add_columns(df):
        """增加字段：是否冲账、amount，修改值：收/支、amount"""
        df = df.sort_values(by='交易时间', axis=0, ascending=False).reset_index(drop=True)
        # 增加字段：是否冲账
        df.insert(df.columns.tolist().index('金额'), '是否冲账', 0)
        df = df.apply(process_excluded_row, axis='columns')  # 修改收支列和增加amount列
        df['category'] = df.apply(process_category_row, axis='columns')  # 修改类别列
        return df

    def check_balance(self):
        """
        和微信支付宝自带汇总数据对账，校验数据
        """
        if np.isclose(self.balance, self.sums.sum()):
            print(f'√ 账单对账成功，支出金额：￥{self.sums['支出']}，收入金额：￥{self.sums['收入']}，结余金额：￥{self.balance}')
        else:
            # TODO: 需要处理跨越订单导致误差
            # raise ValueError(f'{self.data_source}账单对账异常，请检查数据！')
            pass

    def check_bank_account(self, bank_balance, bank_name='民生银行储蓄卡(4827)'):
        sums = self.df[self.df['支付方式'] == bank_name].groupby('收/支')['金额'].sum()
        balance = np.round(sums['收入'] - sums['支出'], 2)
        if balance != bank_balance:
            message = f'银行卡对账单异常，预期余额：￥{bank_balance}, 实际余额：￥{balance}'
            raise ValueError(message)
        else:
            income = sums.get('收入', 0)
            expenditure = sums.get('支出', 0)
            print(f'√ 账单对账成功，收入金额：￥{income}, 支出金额：￥{expenditure}, 结余金额：￥{balance}')
            return True

    def write(self):
        with open('data/transaction_record.csv', 'a', newline='', encoding='utf-8') as f:
            self.df.to_csv(f, header=f.tell() == 0, index=False)

    def __repr__(self):
        """返回 DataFrame 的字符串表示"""
        return self.df.__repr__()


class WeixinProcessor(Processor):
    @property
    def file_encoding(self):
        return "utf-8"

    @property
    def balance(self):
        return super().balance
    #
    # @property
    # def df(self):
    #     """将已存入零钱的交易，交易账户改为“零钱”"""
    #     return self.read_data()

    def read_data(self):
        df = pd.read_csv(
            self.path, header=16, usecols=[0, 1, 2, 3, 4, 5, 6, 7],
            skipfooter=0,
            encoding=self.file_encoding
        )  # 数据获取，微信

        df = self.strip_in_data(df)  # 去除列名与数值中的空格。
        df['交易时间'] = pd.to_datetime(df['交易时间'])  # 数据类型更改
        df['金额(元)'] = df['金额(元)'].astype('float64')  # 数据类型更改

        df = df.apply(self.clean_weixin_payment_method, axis='columns')
        df['category'] = df.apply(process_category_row, axis='columns')
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
        return df

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

    def read_data(self):  # 获取支付宝数据
        """
        支付宝账单编码方式：GBK
        :return:
        """
        df = pd.read_csv(self.path, header=22, encoding='gbk')  # 支付宝
        df['交易时间'] = pd.to_datetime(df['交易时间'])  # 数据类型更改
        df['金额'] = df['金额'].astype('float64')  # 数据类型更改

        selected_columns = ['交易时间', '收/支', '交易状态', '交易分类', '交易对方', '商品说明', '金额', '收/付款方式']
        df = df[selected_columns]  # 按顺序提取所需列
        df.rename(columns={
            '交易分类': 'category',
            '交易状态': '支付状态',
            '商品说明': '商品',
            '收/付款方式': '支付方式'},
            inplace=True)  # 修改列名称
        # 增加字段：来源、类型
        df.insert(1, '来源', self.data_source, allow_duplicates=True)  # 添加支付宝来源标识
        df.insert(4, '类型', "商户消费", allow_duplicates=True)
        return df

    @staticmethod
    def filter_data(df):
        """过滤有退款的交易。条件是：收/支=不计收支 & 支付状态=交易关闭"""
        return df[(df['支付状态'] != '交易关闭') & (df['收/支'] != '不计收支')]

    @staticmethod
    def clean_data(df):
        return df.apply(clean_alipay_payment_method, axis='columns')

    def process_data(self):
        df = self.read_data()
        df = self.add_columns(df)
        df = self.clean_data(df)
        df = self.filter_data(df)
        return df

    @property
    def df(self):
        return self.process_data()


def clean_alipay_payment_method(row):
    """
    去掉支付宝的支付方式后缀，整理格式例如：'光大银行信用卡(5851)'
    :return: str
    """
    if row['收/支'] == '收入' and pd.isnull(row['支付方式']):
        row['支付方式'] = '余额宝'
    row['支付方式'] = str(row['支付方式'])[:13]
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


def process_category_row(row):
    """识别交易类别"""
    text = row['交易对方'] + ' ' + row['商品']
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
    filepath="微信支付账单(20250101-20250131)——【解压密码可在微信支付公众号查看】.csv"
    res = load_to_df(filepath)