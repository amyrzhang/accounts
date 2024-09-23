# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from uploader import Processor


class Analyzer(Processor):
    def __init__(self):
        self.path = 'data/transaction_record.csv'
        self._df = pd.read_csv(self.path)
        self._df.sort_values(by='交易时间', ascending=False, inplace=True)

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        self._df = value

    @property
    def max_month(self):
        return pd.to_datetime(self._df['交易时间']).max().strftime('%Y-%m')

    def rename(self):
        self._df.rename(
            inplace=True,
            columns={
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
            },
        )

    def filter_monthly(self):
        self._df = self._df[self._df['交易时间'].str.startswith(self.max_month)]

    def filter(self, params):
        """
        筛选数据，遍历 ImmutableMultiDict 对象
        :param params:
        :return:
        """
        for param, value in params.items():
            if param in self._df.columns:
                self._df = self._df[self._df[param].astype(str).str.contains(value)]
            else:
                print(f"Warning: Column '{param}' not found in DataFrame.")
