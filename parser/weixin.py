#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from .base import Processor


class WeixinProcessor(Processor):
    HEADER_ROW = 16
    COLUMNS = [0, 1, 2, 3, 4, 5, 6, 7]

    COLUMN_MAPPING = {
        '交易时间': 'time',
        '来源': 'source',
        '收/支': 'debit_credit',
        '当前状态': 'status',
        '交易类型': 'type',
        '交易对方': 'counterparty',
        '商品': 'goods',
        '金额(元)': 'amount',
        '支付方式': 'payment_method'
    }
    DATA_SOURCE = "微信"
    FILE_ENCODING = 'utf-8'

    @property
    def balance(self):
        return super().balance

    @property
    def df(self):
        """获取微信数据"""
        try:
            df = self._load_data()
        except Exception as e:
            raise ValueError(f"读取文件失败: {e}")

        # 列重命名
        df = df.rename(columns=self.COLUMN_MAPPING)

        # 数据预处理
        df = self._preprocess_data(df)

        # 添加计算字段
        df = self._add_computed_fields(df)

        # 最终验证
        if self.check_balance(df):
            return df
        return None

    def _load_data(self):
        """加载数据"""
        if self.path.lower().endswith('.xlsx'):
            return self._read_xlsx()
        else:
            return self._read_csv()

    def _preprocess_data(self, df):
        """数据预处理"""
        # 去除金额字段的货币符号
        df['amount'] = pd.to_numeric(df['amount'].str.replace('¥', ''), errors='coerce')
        # 推断支付方式
        df = df.apply(self._inference_payment_method, axis=1)
        return df

    def _add_computed_fields(self, df):
        """添加计算字段"""
        # 推断分类
        df['category'] = df.apply(self.inference_category, axis=1)
        # 设置数据源
        df['source'] = self.DATA_SOURCE
        return df

    def _read_csv(self):
        """读取微信CSV格式账单"""
        return pd.read_csv(
            self.path,
            header=self.HEADER_ROW,
            usecols=self.COLUMNS,
            skipfooter=0,
            encoding=self.FILE_ENCODING,
            engine='python'  # 支持 skipfooter
        )

    def _read_xlsx(self):
        """读取微信XLSX格式账单"""
        return pd.read_excel(
            self.path,
            header=self.HEADER_ROW,
            usecols=self.COLUMNS,
            skipfooter=0
        )

    @staticmethod
    def _inference_payment_method(row):
        """微信收入的交易账户为 零钱 """
        if row['debit_credit'] == '收入' and row['payment_method'] == '/' and row['status'] == "已存入零钱":
            row['payment_method'] = '零钱'
        return row
