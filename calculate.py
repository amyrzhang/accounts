# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from uploader import Processor


class Analyzer(Processor):
    def __init__(self, month=None):
        self.path = 'output/transaction_record.csv'
        self._df = pd.read_csv(self.path)
        self._month = month
        self.filter()

    @property
    def selected_month(self):
        if self._month is not None:
            return self._month
        else:
            return self._df['month'].max()

    def filter(self):
        self._df['交易时间'] = pd.to_datetime(self._df['交易时间'])
        self._df['month'] = self._df['交易时间'].dt.to_period('M')  # 格式：'2024-05'
        self._df = self._df[self._df['month'] == self.selected_month]

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        self._df = value
