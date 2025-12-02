#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# app/utils/import_service.py
import logging

# 更新导入路径
from parser import WeixinProcessor, AlipayProcessor

class ImportService:
    @staticmethod
    def import_cashflow(file_path):
        try:
            if '微信支付账单' in str(file_path):
                bill = WeixinProcessor(file_path)
                return bill.df.to_dict(orient='records')
            if 'alipay_record' in str(file_path) or '支付宝' in str(file_path):
                bill = AlipayProcessor(file_path)
                return bill.df.to_dict(orient='records')
            return {'error': f'Unsupported file type: {file_path}'}, 400
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
            return {'error': f'Error processing file: {file_path}'}, 500


if __name__ == '__main__':
    filepath= "../../支付宝交易明细(20250401-20250430).csv"
    res = ImportService.import_cashflow(filepath)
