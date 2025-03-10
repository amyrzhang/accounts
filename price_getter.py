# -*- coding: utf-8 -*-
from typing import Any

import akshare as ak
from datetime import datetime
import requests
import pandas as pd

from sqlalchemy import column

from model import db, StockPrice

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


def insert_stock_data(stock_code):
    """
    获取股票日线数据
    :param stock_code: 股票代码
    :return: 股票数据
    """
    df = ak.stock_zh_a_hist(
        symbol=stock_code, period="daily",
        start_date="20000101", end_date=datetime.now().strftime("%Y%m%d"), adjust=""
    )
    df.rename(columns=column_map, inplace=True)
    df.to_sql('stock_price', con=db.engine, if_exists='append', index=False)
    print({'stock_code': stock_code, 'records': df.shape[0], 'from_date': df['date'].min(), 'to_date': df['date'].max()})


def query_stock_price(
    stock_code: str,
    start_date: str = None,
    end_date: str = None
) -> Any | None:
    start_date = start_date or "2000-01-01"
    end_date = end_date or datetime.now().strftime("%Y-%m-%d")
    url = "https://stockapi.com.cn/v1/base/day"
    params = {
        "code": stock_code,
        "startDate": start_date,
        "endDate": end_date,
        "calculateCycle": "100",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    if not (data_json["data"]):
        return None
    return transform_stock_data(data_json["data"])


def transform_stock_data(original_data):
    # 键名映射规则
    key_mapping = {
        "code": "stock_code",
        "time": "date",
        "turnoverRatio": "turnover",
        "change": "change_amount",
        "changeRatio": "change_percentage"
    }

    processed_data = []
    for item in original_data:
        new_item = {}
        for key, value in item.items():
            # 处理键名映射
            if key in key_mapping:
                new_key = key_mapping[key]

                # 特殊处理股票代码值
                if key == "code":
                    new_value = value.split('.')[0]  # 去除后缀
                else:
                    new_value = value

                new_item[new_key] = new_value
            else:
                # 保留其他字段
                new_item[key] = value
        processed_data.append(new_item)

    return processed_data


def create_stock_data(stock_code, start_date=None, end_date=None):
    records = query_stock_price(stock_code=stock_code, start_date=start_date, end_date=end_date)
    created_stock_price = []

    for data in records:
        # 查询是否存在相同记录
        existing_stock_price = StockPrice.query.filter(
            StockPrice.stock_code == data.get('stock_code'),
            StockPrice.date == data.get('date')
        ).first()

        if not existing_stock_price:
            stock_price = StockPrice(
                date=data.get('date'),
                stock_code=data.get('stock_code'),
                open=data.get('open'),
                close=data.get('close'),
                high=data.get('high'),
                low=data.get('low'),
                volume=data.get('volume'),
                amount=data.get('amount'),
                change_percentage=data.get('change_percentage'),
                change_amount=data.get('change_amount'),
                turnover=data.get('turnover')
            )
            db.session.add(stock_price)
            created_stock_price.append(stock_price)

    db.session.commit()
    return created_stock_price


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


if __name__ == '__main__':
    stock_list = ['002991', '603345']
    res = query_stock_price(stock_list[0], "2025-03-10", "2025-03-10")
    print(res)
