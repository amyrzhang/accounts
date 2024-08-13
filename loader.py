#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import re
import warnings
import pandas as pd


def load_data():
    # 读取数据
    recorder = WeixinTransactions()
    recorder.path = 'data/微信支付账单(20240701-20240801).csv'
    data_weixin = recorder.load_data_weixin()

    recorder = AlipayTransactions()
    recorder.path = 'data/alipay_record_20240801_165204.csv'
    data_alipay = recorder.load_data_alipay()  # 读数据
    data_bank = read_data_bank('data/bank_record.csv')

    # 检查账单
    check_bill_data(data_weixin)
    check_bill_data(data_alipay)
    check_bill_data(data_bank)

    # 合并数据
    data_merge = pd.concat([data_weixin, data_alipay], axis=0, ignore_index=True)
    data_merge = pd.concat([data_merge, data_bank], axis=0, ignore_index=True)  # 上下拼接合并表格
    data_merge = data_merge.sort_values(by='交易时间', axis=0, ascending=False).reset_index()
    # data_merge.to_csv('data/merged_data.csv', encoding='gbk')

    # 标记并修改数据
    col_values = [0,
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
    es_df = EqualSumDataFrame(data_merge)
    es_df.add_cols()
    es_df.update_struct_balance(col_values)
    print("已自动计算乘后金额和交易月份，已合并数据")

    # 检查合并数据
    date_range = check_bill_data(data_merge)

    # 写入数据
    write_record_data(data_merge)

    return data_merge


class WeixinTransactions:
    def __init__(self):
        self.path = ''
        self.incomes = 0
        self.expenditures = 0
        self.balance = 0
        self.data_weixin = pd.DataFrame()

    def extract_summary(self):
        # 校验数据
        with open(self.path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.incomes = float(re.findall(r'笔 (.+?)元', lines[7])[0])
            self.expenditures = float(re.findall(r'笔 (.+?)元', lines[8])[0])
            self.balance = round(self.incomes - self.expenditures, 2)
        return

    def read_data_weixin(self):  # 获取微信数据
        d_weixin = pd.read_csv(self.path, header=16, skipfooter=0, encoding='utf-8')  # 数据获取，微信
        selected_columns = ['交易时间', '收/支', '当前状态', '交易类型', '交易对方', '商品', '金额(元)', '支付方式']
        d_weixin = d_weixin[selected_columns]  # 按顺序提取所需列
        d_weixin = strip_in_data(d_weixin)  # 去除列名与数值中的空格。
        d_weixin['交易时间'] = pd.to_datetime(d_weixin['交易时间'])  # 数据类型更改
        d_weixin['金额(元)'] = d_weixin['金额(元)'].astype('float64')  # 数据类型更改
        d_weixin.rename(columns={'当前状态': '支付状态', '交易类型': '类型', '金额(元)': '金额'}, inplace=True)  # 修改列名称
        d_weixin.insert(1, '来源', "微信", allow_duplicates=True)  # 添加微信来源标识

        # 校验数据
        actual_incomes = sum(d_weixin[d_weixin['收/支'] == '收入']['金额'])
        actual_expenditures = sum(d_weixin[d_weixin['收/支'] == '支出']['金额'])

        if not (np.isclose(self.incomes, actual_incomes) and np.isclose(self.expenditures, actual_expenditures)):
            warnings.warn('微信账单数据读取异常，请检查数据！', UserWarning)

        # 打印成功信息
        print("成功读取 " + str(d_weixin.shape[0]) + " 条「微信」账单数据\n")
        return d_weixin

    def load_data_weixin(self):
        # 读取数据
        self.extract_summary()
        data = self.read_data_weixin()

        # 处理【支付方式】和【金额】
        data = data.apply(clean_weixin_payment_method, axis='columns')
        self.data_weixin = data
        return data


class AlipayTransactions:
    def __init__(self):
        self.path = ''
        self.incomes = 0
        self.expenditures = 0
        self.balance = 0
        self.data_alipay = pd.DataFrame()

    def extract_summary(self):
        with open(self.path, 'r', encoding='gbk') as f:
            lines = f.readlines()
            self.incomes = float(re.findall(r'笔 (.+?)元', lines[8])[0])
            self.expenditures = float(re.findall(r'笔 (.+?)元', lines[9])[0])
            self.balance = round(self.incomes - self.expenditures, 2)
            return

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

        # 打印成功信息
        len2 = len(d_alipay)
        print("成功读取 " + str(len2) + " 条「支付宝」账单数据\n")

        return d_alipay

    def load_data_alipay(self):
        """
        过滤有退款的交易。条件是：收/支=不计收支 & 支付状态=交易关闭
        :return: pd.DataFrame
        """
        self.extract_summary()
        data_alipay = self.read_data_alipay()
        data_alipay = data_alipay.apply(clean_alipay_payment_method, axis='columns')

        # 过滤数据
        data_alipay = data_alipay[(data_alipay['支付状态'] != '交易关闭') & (data_alipay['收/支'] != '不计收支')]

        # 校验数据
        actual_incomes = sum(data_alipay[data_alipay['收/支'] == '收入']['金额'])
        actual_expenditures = sum(data_alipay[data_alipay['收/支'] == '支出']['金额'])

        if not (np.isclose(self.incomes, actual_incomes) and np.isclose(self.expenditures, actual_expenditures)):
            warnings.warn('支付宝账单数据读取异常，请检查数据！', UserWarning)

        self.data_alipay = data_alipay
        return data_alipay


def write_record_data(merged):
    # 文件路径
    date_range = check_bill_data(merged, is_mute=True)
    file_name = 'data/record_{}'.format(date_range)

    # 写入数据
    merged.to_csv(file_name + '.csv'.format(file_name), index=False)
    merged.to_excel(file_name + '.xlsx', index=False)
    return merged


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


def clean_amount(row):
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
    if row['来源'] != '微信':
        return row

    status = row['支付状态']
    amount = row['金额']
    match = re.search(r"(已退款)[(]?￥(\d+\.\d+)[)]?", status)
    if match:  # 如果部分退款
        amount -= float(match.group(2))
    elif status == '已全额退款':  # 如果全额退款
        if amount != 11:  # TODO: 开发自动成对冲账功能
            row['收/支'] = '不计收支'
            amount = 0

    # 考虑收支添加符号
    row['amount'] = amount if row['收/支'] == '收入' else -amount
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


def clean_record_amount(row):
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
    amount = row['金额']

    # 修改微信 不计入收支
    if row['来源'] == '微信' and row['支付状态'] == '已全额退款':  # 如果全额退款
        if amount != 11:  # TODO: 开发自动成对冲账功能
            row['收/支'] = '不计收支'

    # 修改微信 部分退款
    match = re.search(r"(已退款)[(]?￥(\d+\.\d+)[)]?", row['支付状态'])
    if match:  # 如果部分退款
        amount -= float(match.group(2))

    # 考虑收支添加符号
    if row['收/支'] == '收入':
        row['amount'] = amount
    elif row['收/支'] == '支出':
        row['amount'] = -amount
    else:
        row['amount'] = 0
    return row


def check_bill_data(bill_data, is_mute=False):
    data_resource = bill_data['来源'].unique()
    min_date, max_date = str(min(bill_data['交易时间']))[:10], str(max(bill_data['交易时间']))[:10]
    bill_date_range = min_date + '至' + max_date
    bill_num = bill_data.shape[0]
    bill_summary = bill_data.groupby('收/支')['金额'].sum()

    # TODO：有可能索引不出来收支数据
    summary = """
    账单来源：{}
    账单周期：{}
    账单数量：{}条
    支出金额：￥{}
    收入金额：￥{}
    结余金额：￥{}
    """.format(data_resource, bill_date_range, bill_num, bill_summary['支出'], bill_summary['收入'],
               bill_summary['收入'] - bill_summary['支出'])

    if not is_mute:
        print(summary)
    return bill_date_range


class EqualSumDataFrame:
    def __init__(self, df, col1='金额', col2='amount'):
        """
        初始化 EqualSumDataFrame 对象

        参数:
        - data: dict, 初始化 DataFrame 的数据
        - col1: str, 第一列的列名
        - col2: str, 第二列的列名
        """
        self.df = pd.DataFrame(df)
        self.col1 = col1
        self.col2 = col2
        self.balance = np.round(self.df[self.df['收/支'] == '收入'][self.col1].sum() - self.df[self.df['收/支'] == '支出'][self.col1].sum(), 2)
        self.incomes = 0
        self.expenditures = 0

    def update_sums(self):
        """
        更新收入和、支出和
        """
        self.incomes = np.round(self.df[self.df['收/支'] == '收入'][self.col2].sum(), 2)
        self.expenditures = np.round(self.df[self.df['收/支'] == '支出'][self.col2].sum(),2)

    def _check_equal_sum(self):
        """
        检查两列的列和是否相等
        """
        if not np.isclose(self.balance, self.incomes + self.expenditures):
            raise ValueError(f"{self.col1} 和 {self.col2} 列和不相等")

    def add_cols(self):  # 增加3列数据
        """
        增加两列：是否不计入收支和是否冲账，并检查列和
        """
        self.df = self.df.apply(clean_record_amount, axis='columns')  # 增加不计收支列，修改数据
        self.df.insert(self.df.columns.tolist().index('金额'), '是否冲账', 0, allow_duplicates=True)  # 增加是否冲账列
        self.update_sums()
        self._check_equal_sum()

    def update_struct_balance(self, col_values):
        """
        更新特定位置的值并检查列和
        :param col_values: 要更新的列值
        :return:
        """
        # 修改是否冲账
        self.df['是否冲账'] = col_values

        # 修改金额
        remaining_amount = self.df['amount'][self.df['是否冲账'] == 1].sum()
        if remaining_amount >= 0:
            index = self.df[(self.df['是否冲账'] == 1) & (self.df['收/支'] == '收入')].index[0]
        else:
            index = self.df[(self.df['是否冲账'] == 1) & (self.df['收/支'] == '支出')].index[0]

        self.df.loc[self.df['是否冲账'] == 1, 'amount'] = 0
        self.df.at[index, 'amount'] = remaining_amount
        self.update_sums()
        self._check_equal_sum()

    def __repr__(self):
        return self.df.__repr__()


