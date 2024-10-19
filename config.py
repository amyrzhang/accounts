# ∞¸∫¨ ˝æ›ø‚≈‰÷√
import os
from urllib.parse import quote_plus as urlquote

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # mysql ≈‰÷√
    MYSQL_USERNAME = "root"
    MYSQL_PASSWORD = "amy24%Bella"
    MYSQL_HOST = "127.0.0.1"
    MYSQL_PORT = 3306
    MYSQL_DATABASE = "money_track"

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USERNAME}:{urlquote(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
