#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from .base import Processor


class AlipayProcessor(Processor):
    # 定义读取列索引
    COLUMNS = [0, 2, 4, 5, 6, 7, 8]

    # 定义列名映射常量
    COLUMN_MAPPING = {
        '交易时间': 'time',
        '交易对方': 'counterparty',
        '商品说明': 'goods',
        '收/支': 'debit_credit',
        '金额': 'amount',
        '收/付款方式': 'payment_method',
        '交易状态': 'status',
    }

    DATA_SOURCE = '支付宝'
    FILE_ENCODING = 'gbk'

    def __init__(self, path):
        super().__init__(path)

    @property
    def balance(self):
        return super().balance

    @property
    def df(self):  # 获取支付宝数据
        try:
            df = self._load_data()
        except FileNotFoundError:
            raise ValueError("文件未找到，请检查路径是否正确")
        except pd.errors.ParserError as e:
            raise ValueError(f"文件解析失败: {e}")
        except Exception as e:
            raise ValueError(f"读取文件失败: {e}")

        # 验证必要字段
        self._validate_required_columns(df)

        # 列重命名
        df.rename(columns=self.COLUMN_MAPPING, inplace=True)

        # 数据预处理
        df = self._preprocess_data(df)

        # 数据过滤
        df = self._filter_data(df)

        # 添加额外字段
        df = self._add_additional_fields(df)

        # 最终验证
        if self.check_balance(df):
            return df
        return None

    def _load_data(self):
        """加载数据"""
        if self.path.endswith('.xlsx'):
            return self._read_xlsx()
        else:
            return self._read_csv()

    def _validate_required_columns(self, df):
        """验证必要字段是否存在"""
        required_columns = list(self.COLUMN_MAPPING.keys())
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"文件缺少必要列: {missing_columns}")

    def _preprocess_data(self, df):
        """数据预处理"""
        # 数据类型更改
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

        # 处理 NaN 值
        df['counterparty'] = df['counterparty'].fillna('')

        # 多账户合并付款，以 & 分隔，需手工整理
        df = df.apply(self._inference_payment_method, axis=1)

        return df

    @staticmethod
    def _filter_data(df):
        """过滤数据"""
        return df[(df['status'].isin(['交易成功', '支付成功'])) &
                  (df['debit_credit'].isin(['收入', '支出']))]

    def _add_additional_fields(self, df):
        """添加额外字段"""
        # 增加字段：类型 type，类别 category、来源 source
        df.insert(1, 'type', "商户消费")
        df["category"] = df.apply(self.inference_category, axis=1)
        df["source"] = self.DATA_SOURCE
        return df

    def _read_csv(self):
        """读取支付宝CSV格式账单"""
        return pd.read_csv(
            self.path, header=22, usecols=self.COLUMNS,
            encoding=self.FILE_ENCODING
        )

    def _read_xlsx(self):
        """读取支付宝XLSX格式账单"""
        return pd.read_excel(
            self.path, header=22, usecols=self.COLUMNS
        )

    @staticmethod
    def _inference_payment_method(row):
        """
        多账户合并付款，以 & 分隔，需手工整理
        去掉支付宝的支付方式后缀，整理格式例如：'光大银行信用卡(5851)'
        :return: str
        """
        payment_method = row['payment_method']
        if row['debit_credit'] == '收入' and pd.isnull(payment_method):
            payment_method = '余额宝'
        # 避免硬编码截断，保留原始信息或按需处理
        row['payment_method'] = str(payment_method).split('&')[0].strip()  # 取首个支付方式
        return row
