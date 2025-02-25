# stock_price_updater.py
import datetime
import logging
import time
from sqlalchemy import func
from apscheduler.schedulers.blocking import BlockingScheduler
from model import db, StockPrice
from price_getter import insert_stock_data, insert_fund_data

# ������־
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
    """��ȡָ����Ʊ����������"""
    latest_date = db.session.query(func.max(StockPrice.date)).filter(
        StockPrice.stock_code == stock_code
    ).scalar()
    return latest_date or datetime.date(2000, 1, 1)


def update_stock_prices():
    """�������й�Ʊ�۸�"""
    with app.app_context():
        try:
            # ��ȡ����Ψһ��Ʊ����
            stock_codes = [code[0] for code in db.session.query(
                StockPrice.stock_code
            ).distinct().all()]

            for code in stock_codes:
                try:
                    latest_date = get_latest_date(code)
                    start_date = (latest_date + datetime.timedelta(days=1)).strftime("%Y%m%d")

                    logger.info(f"���ڸ��� {code} ���ݣ���ʼ���ڣ�{start_date}")

                    # ��Ʊ�����ʽ��������akshareҪ��
                    if code.startswith(('5', '6', '9')):
                        symbol = f"{code}.SH"
                    else:
                        symbol = f"{code}.SZ"

                    # ��ȡ���ݲ�����
                    insert_stock_data(symbol)
                    time.sleep(1)  # ��ֹ�������Ƶ��

                except Exception as e:
                    logger.error(f"���� {code} ʧ��: {str(e)}")
                    continue

            logger.info("��Ʊ�۸�������")

        except Exception as e:
            logger.error(f"��������ִ��ʧ��: {str(e)}")


if __name__ == "__main__":
    from app import app  # ����FlaskӦ��ʵ��

    # ��ʼ��������
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # ÿ���賿1��ִ��
    scheduler.add_job(
        update_stock_prices,
        'cron',
        hour=1,
        minute=0,
        misfire_grace_time=60  # ����60���ڵĴ������
    )

    try:
        logger.info("������Ʊ�۸���¶�ʱ����...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("��ֹͣ��ʱ����")
