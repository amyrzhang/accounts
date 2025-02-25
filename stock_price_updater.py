# stock_price_updater.py
import datetime
import logging
import time
from sqlalchemy import func
from apscheduler.schedulers.blocking import BlockingScheduler
from model import db, StockPrice
from price_getter import insert_stock_data, insert_fund_data

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('stock_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_latest_date(stock_code):
    """获取指定股票的最新日期"""
    latest_date = db.session.query(func.max(StockPrice.date)).filter(
        StockPrice.stock_code == stock_code
    ).scalar()
    return latest_date or datetime.date(2000, 1, 1)


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
                    start_date = (latest_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

                    logger.info(f"正在更新 {code} 数据，起始日期：{start_date}")

                    # 股票代码格式处理（根据akshare要求）
                    if code.startswith(('5', '6', '9')):
                        symbol = f"{code}.SH"
                    else:
                        symbol = f"{code}.SZ"

                    # 获取数据并插入
                    insert_stock_data(symbol)
                    time.sleep(1)  # 防止请求过于频繁

                except Exception as e:
                    logger.error(f"更新 {code} 失败: {str(e)}")
                    continue

            logger.info("股票价格更新完成")

        except Exception as e:
            logger.error(f"更新任务执行失败: {str(e)}")


if __name__ == "__main__":
    from app import app  # 导入Flask应用实例

    # 初始化调度器
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # 每天凌晨1点执行
    scheduler.add_job(
        update_stock_prices,
        'cron',
        hour=1,
        minute=0,
        misfire_grace_time=60  # 允许60秒内的错过触发
    )

    try:
        logger.info("启动股票价格更新定时任务...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("已停止定时任务")
