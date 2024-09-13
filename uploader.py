#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import re
import pandas as pd
import os
import json
import chardet


def write_db(filename):
    if filename.startswith('微信支付账单'):
        wxt = WeixinTransactions(filename)  # 写入数据
        wxt.write_data()
    elif filename.startswith('alipay_record'):
        alipay = AlipayTransactions(filename)  # 写入数据


def check_balance(balance, df):
    """
    和微信支付宝自带汇总数据对账，校验数据
    """
    incomes = sum(df[df['收/支'] == '收入']['金额'])
    expenditures = sum(df[df['收/支'] == '支出']['金额'])
    if np.round(incomes - expenditures, 2) != balance:
        raise ValueError('账单对账异常，请检查数据！')
    else:  # TODO：有可能索引不出来收支数据
        print('√ 账单对账成功，支出金额：￥{}，收入金额：￥{}，结余金额：￥{}'.format(expenditures, incomes, balance))
        return True


class Transactions:
    def __init__(self, path):
        self.path = path

    @property
    def balance(self):
        with open(self.path, 'r', encoding=self.encoding) as f:
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
    def sums(self):
        return np.round(self.df.groupby(['收/支'])['amount'].sum(), 2)

    @property
    def category_sums(self):
        return self.df.groupby(['收/支', 'category'])['amount'].sum().sort_values()

    @property
    def date_range(self):
        max_date = self.df['交易时间'].max().strftime('%Y%m%d')
        min_date = self.df['交易时间'].min().strftime('%Y%m%d')
        return min_date + '_' + max_date

    @property
    def labeled_dict(self):
        """需要手动标记存入数据"""
        file_path = 'labeled_record_{}.xlsx'.format(self.date_range)
        labeled = pd.read_excel(file_path, usecols=['是否冲账', 'category'])
        return labeled.to_dict(orient='list')

    @property
    def encoding(self):
        with open(self.path, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            return result['encoding']

    def add_columns(self):
        self.df = self.df.sort_values(by='交易时间', axis=0, ascending=False).reset_index(drop=True)
        self.df.insert(self.df.columns.tolist().index('金额'), '是否冲账', 0)  # 增加是否冲账列
        self.df.insert(self.df.columns.tolist().index('交易对方'), 'category', '餐饮')  # 增加类别列
        self.df = self.df.apply(process_excluded_row, axis='columns')  # 修改收支列和增加amount列
        self.df['category'] = self.df.apply(process_category_row, axis='columns')  # 修改不计收支值，修改金额

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, new_df):
        self._df = new_df

    def __repr__(self):
        """返回 DataFrame 的字符串表示"""
        return self.df.__repr__()

    def update_columns(self):
        """
        更新列值，其中键是要更新的列名，值是要设置的新值
        """
        for col, new_value in self.labeled_dict.items():
            if col in self._merged_df.columns:
                self._merged_df[col] = new_value

        # 将修改后的 DataFrame 重新设置回 df 属性，以触发 setter
        self.df = settle_transactions(self._merged_df)
        self._check_equal_sum()

    def _check_equal_sum(self):
        """
        检查两列的列和是否相等
        """
        if not np.isclose(self.balance, self.sums.sum()):
            raise ValueError(f"{'金额'} 和 {'amount'} 列和不相等")

    def check_bank_account(self, bank_balance, bank_name='民生银行储蓄卡(4827)'):
        sums = self.df[self.df['支付方式'] == bank_name].groupby('收/支')['金额'].sum()
        balance = np.round(sums['收入'] - sums['支出'], 2)
        if balance != bank_balance:
            message = '银行卡对账单异常，预期余额：￥{}, 实际余额：￥{}'.format(bank_balance, balance)
            raise ValueError(message)
        else:
            income = sums.get('收入', 0)
            expenditure = sums.get('支出', 0)
            print('√ 账单对账成功，收入金额：￥{}, 支出金额：￥{}, 结余金额：￥{}'.format(income, expenditure, balance))
            return True

    def update_struct_balance(self, col_values):
        """
        更新特定位置的值并检查列和
        :param col_values: 要更新的列值
        :return:
        """
        self.df['是否冲账'] = col_values  # 修改是否冲账
        remaining_amount = self.df['amount'][self.df['是否冲账'] == 1].sum()
        if remaining_amount >= 0:
            index = self.df[(self.df['是否冲账'] == 1) & (self.df['收/支'] == '收入')].index[0]
        else:
            index = self.df[(self.df['是否冲账'] == 1) & (self.df['收/支'] == '支出')].index[0]
        self.df.loc[self.df['是否冲账'] == 1, 'amount'] = 0
        self.df.at[index, 'amount'] = remaining_amount  # 修改金额
        self._check_equal_sum()


class WeixinTransactions(Transactions):
    @property
    def balance(self):
        return super().balance

    @property
    def df(self):
        """将已存入零钱的交易，交易账户改为“零钱”"""
        df = self.read_data_weixin()  # 读取数据
        df = df.apply(clean_weixin_payment_method, axis='columns')  # 处理【支付方式】和【金额】
        check_balance(self.balance, df)  # 校验数据
        return df

    def read_data_weixin(self):  # 获取微信数据
        d_weixin = pd.read_csv(self.path, header=16, skipfooter=0, encoding='utf-8')  # 数据获取，微信
        # 选择列和数据类型
        selected_columns = ['交易时间', '收/支', '当前状态', '交易类型', '交易对方', '商品', '金额(元)', '支付方式']
        d_weixin = d_weixin[selected_columns]  # 按顺序提取所需列
        d_weixin.rename(columns={'当前状态': '支付状态', '交易类型': '类型', '金额(元)': '金额'}, inplace=True)  # 修改列名称
        d_weixin = strip_in_data(d_weixin)  # 去除列名与数值中的空格。
        d_weixin['交易时间'] = pd.to_datetime(d_weixin['交易时间'])  # 数据类型更改
        d_weixin['金额'] = d_weixin['金额'].astype('float64')  # 数据类型更改

        # 增加列
        d_weixin.insert(1, '来源', "微信", allow_duplicates=True)  # 添加微信来源标识
        d_weixin.insert(d_weixin.columns.tolist().index('金额'), '是否冲账', 0)  # 增加是否冲账列
        d_weixin.insert(d_weixin.columns.tolist().index('交易对方'), 'category', '餐饮')  # 增加类别列

        # 更新数据
        d_weixin = d_weixin.apply(process_excluded_row, axis='columns')  # 修改收支列和增加amount列
        d_weixin['category'] = d_weixin.apply(process_category_row, axis='columns')  # 修改不计收支值，修改金额
        return d_weixin


class AlipayTransactions(Transactions):
    @property
    def balance(self):
        return super().balance

    def read_data_alipay(self):  # 获取支付宝数据
        d_alipay = pd.read_csv(self.path, header=22, encoding='gbk')  # 数据获取，支付宝
        selected_columns = ['交易时间', '收/支', '交易状态', '交易对方', '商品说明', '金额', '收/付款方式']
        d_alipay = d_alipay[selected_columns]  # 按顺序提取所需列
        d_alipay = strip_in_data(d_alipay)  # 去除列名与数值中的空格。
        d_alipay['交易时间'] = pd.to_datetime(d_alipay['交易时间'])  # 数据类型更改
        d_alipay['金额'] = d_alipay['金额'].astype('float64')  # 数据类型更改
        d_alipay = d_alipay.drop(d_alipay[d_alipay['收/支'] == ''].index)  # 删除'收/支'为空的行
        d_alipay.rename(columns={'交易状态': '支付状态', '商品说明': '商品', '收/付款方式': '支付方式'},
                        inplace=True)  # 修改列名称
        d_alipay.insert(1, '来源', "支付宝", allow_duplicates=True)  # 添加支付宝来源标识
        d_alipay.insert(4, '类型', "商户消费", allow_duplicates=True)  # 添加类型标识
        return d_alipay

    @property
    def df(self):
        """
        过滤有退款的交易。条件是：收/支=不计收支 & 支付状态=交易关闭
        :return: pd.DataFrame
        """
        data_alipay = self.read_data_alipay()
        data_alipay = data_alipay.apply(clean_alipay_payment_method, axis='columns')

        # 过滤数据
        df = data_alipay[(data_alipay['支付状态'] != '交易关闭') & (data_alipay['收/支'] != '不计收支')]
        check_balance(self.balance, df)
        return df


def strip_in_data(data):  # 把列名中和数据中首尾的空格都去掉。
    data = data.rename(columns={column_name: column_name.strip() for column_name in data.columns})
    data = data.map(lambda x: x.strip().strip('¥') if isinstance(x, str) else x)
    return data


def clean_weixin_payment_method(row):
    """
    将已存入零钱的交易，交易账户改为“零钱”
    :type row: pd.Series
    :return: pd.Series
    """
    if row['支付方式'] == '/' and row['支付状态'] == '已存入零钱':
        row['支付方式'] = '零钱'
    return row


def clean_alipay_payment_method(row):
    """
    去掉支付宝的支付方式后缀，整理格式例如：'光大银行信用卡(5851)'
    :return: str
    """
    if row['收/支'] == '收入' and pd.isnull(row['支付方式']):
        row['支付方式'] = '余额宝'
    row['支付方式'] = str(row['支付方式'])[:13]
    return row


def read_data_bank(path):
    data = pd.read_csv(path)
    data['交易时间'] = pd.to_datetime(data['交易时间'])
    data['金额'] = data['金额'].astype('float64')
    return data


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
    """
    识别交易类别
    :param row:
    :return:
    """
    text = row['交易对方'] + ' ' + row['商品']
    shopping_pattern = '平台商户|抖音电商商家|快递'  # 根据交易对方判断
    transportation_pattern = '出行|加油|中铁|12306'  # 根据二者判断
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

