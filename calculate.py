# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np


def _load():
    df = pd.read_csv('./output/record_20240701_20240731.csv')
    df['交易时间'] = pd.to_datetime(df['交易时间'])
    df['year'] = df['交易时间'].dt.year
    df['quarter'] = df['交易时间'].dt.quarter
    df['month'] = df['交易时间'].dt.month
    df['week'] = df['交易时间'].dt.isocalendar().week
    return df


class Analysis:
    def __init__(self):
        self.df = _load()

    @property
    def balance(self):
        """计算收支平衡"""
        summary = self.df.groupby('收/支')['金额'].sum()
        return np.round(summary['收入'] - summary['支出'], 2)

    @property
    def sums(self):
        return np.round(self.df.groupby(['收/支'])['amount'].sum(), 2)

    @property
    def category_sums(self):
        return self.df.groupby(['收/支', 'category'])['amount'].sum().sort_values()

    @property
    def monthly_summary(self):
        return {
            'expenditure': self.sums['收入'],
            'income': self.sums['支出'],
            'balance': self.balance
        }

