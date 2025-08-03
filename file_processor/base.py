#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import pandas as pd

class Processor:
    def __init__(self, path):
        self.path = path
        self._df = pd.DataFrame()

    @property
    def balance(self):
        """获取文件中的余额信息"""
        try:
            # 确定文件编码
            file_encoding = self._determine_file_encoding()

            # 根据文件类型读取内容并提取收入和支出
            if self.path.lower().endswith('.xlsx'):
                incomes, expenditures = self._extract_from_xlsx(file_encoding)
            else:
                incomes, expenditures = self._extract_from_text(file_encoding)

            return round(incomes - expenditures, 2)
        except Exception:
            # 如果出现任何错误，返回默认值
            return 0.0

    def _determine_file_encoding(self):
        """确定CSV文件编码格式"""
        if 'alipay' in self.path or '支付宝' in self.path:
            return 'gbk'
        else:
            return 'utf-8'

    def _extract_from_text(self, file_encoding):
        """从文本文件中提取收入和支出"""
        with open(self.path, 'r', encoding=file_encoding) as f:
            text = f.read()
            return self._extract_income_expense_from_text(text)

    def _extract_from_xlsx(self, file_encoding):
        """从Excel文件中提取收入和支出"""
        try:
            # 读取Excel文件的前几行和后几行寻找汇总信息
            # 读取前30行
            df_head = pd.read_excel(self.path, header=None, nrows=30)
            text_head = df_head.to_string()
            incomes, expenditures = self._extract_income_expense_from_text(text_head)

            # 如果在前几行找到了，直接返回
            if incomes > 0 or expenditures > 0:
                return incomes, expenditures

            # 如果没找到，尝试读取后几行
            excel_file = pd.ExcelFile(self.path)
            for sheet_name in excel_file.sheet_names:
                full_df = pd.read_excel(self.path, sheet_name=sheet_name, header=None)
                total_rows = len(full_df)

                if total_rows > 30:
                    df_tail = pd.read_excel(
                        self.path,
                        sheet_name=sheet_name,
                        header=None,
                        skiprows=total_rows - 30
                    )
                    text_tail = df_tail.to_string()
                    incomes, expenditures = self._extract_income_expense_from_text(text_tail)

                    if incomes > 0 or expenditures > 0:
                        return incomes, expenditures

            return 0, 0
        except Exception:
            return 0, 0

    @staticmethod
    def _extract_income_expense_from_text(text):
        """从文本中提取收入和支出金额"""
        # 定义正则表达式
        income_pattern = r'收入：\d+笔\s+(\d+\.\d+)元'
        expense_pattern = r'支出：\d+笔\s+(\d+\.\d+)元'

        # 搜索并提取收入和支出金额
        income_match = re.search(income_pattern, text)
        incomes = 0
        if income_match:
            incomes = float(income_match.group(1))

        expense_match = re.search(expense_pattern, text)
        expenditures = 0
        if expense_match:
            expenditures = float(expense_match.group(1))

        return incomes, expenditures

    @property
    def df(self):
        return self._df

    def check_balance(self, df):
        if df.empty:
            return None
        sums = df.groupby(['debit_credit'])['amount'].sum()
        if '收入' not in sums:
            sums['收入'] = 0

        balance = round(sums['收入'] - sums['支出'], 2)
        if balance == self.balance:
            return f'{self.path} is checked'
        return None

    @staticmethod
    def inference_category(row):
        """识别交易类别"""
        text = str(row['counterparty']) + ' ' + str(row['goods'])
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
