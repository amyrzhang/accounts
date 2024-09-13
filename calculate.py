# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np


class DataAnalyzer:
    def __init__(self, month=None):
        self._month = month
        self.df = pd.read_csv('./output/record_20240701_20240731.csv')
        self.df['date'] = pd.to_datetime(self.df['交易时间'])
        self.df['month'] = self.df['date'].dt.to_period('M')  # 格式：'2024-05'

    @property
    def month(self):
        if self._month:
            return self._month
        else:
            return self.df['month'].max()

    @property
    def filter_df(self):
        return self.df[self.df['month'] == self.month]

    @property
    def balance(self):
        """计算收支平衡"""
        summary = self.filter_df.groupby('收/支')['金额'].sum()
        return np.round(summary['收入'] - summary['支出'], 2)

    @property
    def sums(self):
        return np.round(self.filter_df.groupby(['收/支'])['amount'].sum(), 2)

    @property
    def category_sums(self):
        return self.filter_df.groupby(['收/支', 'category'])['amount'].sum().sort_values()

    @property
    def monthly_summary(self):
        return {
            'expenditure': -self.sums['支出'],
            'income': self.sums['收入'],
            'balance': self.balance
        }


