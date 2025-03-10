# -*- coding: utf-8 -*-
import akshare as ak
from datetime import datetime

from sqlalchemy import column

from model import db

column_map = {
    '日期': 'date',
    '股票代码': 'stock_code',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'amount',
    '振幅': 'amplitude',
    '涨跌幅': 'change_percentage',
    '涨跌额': 'change_amount',
    '换手率': 'turnover'
}

def insert_stock_data(stock_code, start_date=None):
    """
    获取股票日线数据（添加start_date参数）
    :param stock_code: 股票代码
    :return: 股票数据
    """
    start_date = start_date or "20000101"
    df = ak.stock_zh_a_hist(
        symbol=stock_code, period="daily",
        start_date=start_date,  # 使用动态start_date
        end_date=datetime.now().strftime("%Y%m%d"),
        adjust=""
    )
    df.rename(columns=column_map, inplace=True)
    df.to_sql('stock_price', con=db.engine, if_exists='append', index=False)
    print({'stock_code': stock_code, 'records': df.shape[0], 'from_date': df['date'].min(), 'to_date': df['date'].max()})

def insert_fund_data(fund_code, start_date=None):
    """
    获取场内ETF基金日线数据
    :param fund_code: 基金代码
    :return: 基金数据
    """
    start_date = start_date or "20000101"
    df = ak.fund_etf_hist_em(
        symbol=fund_code,
        start_date=start_date,  # 使用动态start_date
        end_date=datetime.now().strftime("%Y%m%d")
    )
    df.rename(columns=column_map, inplace=True)
    df.insert(1, 'stock_code', fund_code)
    df.to_sql('stock_price', con=db.engine, if_exists='append', index=False)
    print({'fund_code': fund_code, 'records': df.shape[0], 'from_date': df['date'].min(), 'to_date': df['date'].max()})

