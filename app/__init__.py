# -*- coding: utf-8 -*-
# app/__init__.py
import os

from flask import Flask
from flask_cors import CORS
from config import Config
from app.extentions import db
from app.api import api_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 初始化数据库
    db.init_app(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 注册总API蓝图
    app.register_blueprint(api_bp, url_prefix='/api')

    return app