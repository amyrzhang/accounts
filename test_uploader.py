#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch, mock_open, MagicMock
from uploader import AlipayTransactions


# 假设的辅助函数，可能在测试中用到
def mock_clean_alipay_payment_method(df):
    return df


def mock_check_balance(balance, df):
    pass


# 测试代码
class TestAlipayTransactions(unittest.TestCase):

    def setUp(self):
        self.test_path = 'uploads/alipay_record_20240801_165204.csv'
        self.alipay_transactions = AlipayTransactions(self.test_path)

    @patch('uploader.pd.read_csv')
    def test_read_data_alipay(self, mock_read_csv):
        # 设置假设的数据
        mock_df = MagicMock()
        mock_df.columns = ['交易时间', '收/支', '交易状态', '交易对方', '商品说明', '金额', '收/付款方式']
        mock_df.astype = MagicMock(return_value=mock_df)
        mock_df.drop = MagicMock(return_value=mock_df)
        mock_df.rename = MagicMock(return_value=mock_df)
        mock_df.apply = MagicMock(side_effect=mock_clean_alipay_payment_method)

        # 设置读取CSV的返回值
        mock_read_csv.return_value = mock_df

        # 运行待测试的方法
        result_df = self.alipay_transactions.read_data_alipay()

        # 确保返回的DataFrame是正确的
        self.assertEqual(result_df, mock_df)
        mock_read_csv.assert_called_once_with(self.test_path, header=22, encoding='gbk')

    @patch('uploader.open', new_callable=mock_open, read_data="笔 150.00元\n笔 361.12元")
    def test_balance(self, mock_file):
        # 运行待测试的方法
        balance = self.alipay_transactions.balance()

        # 确保计算的余额是正确的
        self.assertEqual(balance, 211.12)
        mock_file.assert_called_once_with(self.test_path, 'r', encoding='gbk')

    @patch('uploader.clean_alipay_payment_method', side_effect=mock_clean_alipay_payment_method)
    @patch('uploader.check_balance', side_effect=mock_check_balance)
    @patch('uploader.AlipayTransactions.read_data_alipay')
    def test_df(self, mock_read_data_alipay, mock_check_balance, mock_clean_alipay_payment_method):
        # 设置假设的数据
        mock_df = MagicMock()
        mock_df.insert = MagicMock(return_value=mock_df)
        mock_df.apply = MagicMock(side_effect=mock_clean_alipay_payment_method)

        # 设置读取数据的返回值
        mock_read_data_alipay.return_value = mock_df

        # 运行待测试的方法
        result_df = self.alipay_transactions.df()

        # 确保返回的DataFrame是正确的
        self.assertEqual(result_df, mock_df)
        mock_read_data_alipay.assert_called_once()


if __name__ == '__main__':
    # unittest.main()
    test_path = 'uploads/alipay_record_20240801_165204.csv'
    alipay_transactions = AlipayTransactions(test_path)
