# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from uploader import Processor


class Analyzer(Processor):
    def __init__(self, month=None):
        self.path = 'data/transaction_record.csv'
        self._df = pd.read_csv(self.path)
        self._month = month
        self.rename()

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        self._df = value

    @property
    def selected_month(self):
        if self._month is not None:
            return self._month
        else:
            return self._df['month'].max()

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
        return self._df

    def filter_by_params(self):
        self._df['交易时间'] = pd.to_datetime(self._df['交易时间'])
        self._df['month'] = self._df['交易时间'].dt.to_period('M')  # 格式：'2024-05'
        self._df = self._df[self._df['month'] == self.selected_month]

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
        return self._df
