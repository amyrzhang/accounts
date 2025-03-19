# -*- coding: utf-8 -*-
import datetime
import logging
import time
import sys
from sqlalchemy import func
from apscheduler.schedulers.blocking import BlockingScheduler
from model import db, StockPrice
from price_getter import create_stock_data, insert_fund_data
from app import app  # 确保正确导入Flask应用实例

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('log/stock_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_latest_date(stock_code):
    with app.app_context():
        latest_date_str = db.session.query(func.max(StockPrice.date)).filter(
            StockPrice.stock_code == stock_code
        ).scalar()

    # 统一转换为 date 对象
    if latest_date_str:
        if isinstance(latest_date_str, str):  # 处理字符串类型
            return datetime.datetime.strptime(latest_date_str, "%Y-%m-%d").date()
        return latest_date_str  # 已经是 date 类型
    else:
        return datetime.date(2000, 1, 1)


def update_stock_prices():
    """更新所有股票价格"""
    with app.app_context():
        try:
            # 获取所有唯一股票代码
            stock_codes = [code[0] for code in db.session.query(
                StockPrice.stock_code
            ).distinct().all()]

            for code in stock_codes:
                try:
                    latest_date = get_latest_date(code)
                    start_date = (latest_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

                    logger.info(f"正在更新 {code} 数据，开始日期：{start_date}")

                    # 判断代码类型（股票/基金）
                    if code.startswith(('60', '000', '001', '002', '003')):  # 沪市&深市主板股票代码规则
                        create_stock_data(code, start_date)
                    if code.startswith('51'):  # 沪市ETF基金代码规则
                        insert_fund_data(code, start_date)
                    # elif code.startswith('15'):  # 深市ETF基金代码规则
                    #     insert_fund_data(code, start_date)

                    time.sleep(1)  # 防止请求过频

                except Exception as e:
                    logger.error(f"更新 {code} 失败: {str(e)}")
                    continue

            logger.info("股票价格更新完成")

        except Exception as e:
            logger.error(f"更新任务执行失败: {str(e)}")


if __name__ == "__main__":
    # 手动更新，命令行参数传入 update_stock_prices
    if len(sys.argv) > 1 and sys.argv[1] == "update_stock_prices":
        update_stock_prices()
    else:
        # 配置定时任务
        scheduler = BlockingScheduler(timezone="Asia/Shanghai")

        # 每天6点执行
        scheduler.add_job(
            update_stock_prices,
            'cron',
            hour=15,
            minute=50,
            misfire_grace_time=60
        )

        try:
            logger.info("启动股票价格自动更新定时任务...")
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            logger.info("终止定时任务")
