# -*- coding: utf-8 -*-
"""
校园社团活动管理系统 —— 配置文件
说明：数据库连接信息可通过环境变量覆盖，未设置时使用默认值。
可在项目根目录创建 .env 文件（参考 .env.example）：
    DB_USERNAME=root
    DB_PASSWORD=你的密码
    DB_HOST=localhost
    DB_PORT=3306
    DB_NAME=club_system
"""
import os

from dotenv import load_dotenv

# 加载项目根目录下的 .env 文件（若存在）
load_dotenv()


class Config:
    """基础配置"""
    # 会话密钥：生产环境务必通过环境变量 SECRET_KEY 覆盖
    SECRET_KEY = os.environ.get('SECRET_KEY', 'club-system-dev-secret-key-change-me')

    # 数据库连接：mysql+pymysql://用户名:密码@主机:端口/库名?charset=utf8mb4
    DB_USERNAME = os.environ.get('DB_USERNAME', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'club_system')

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 开发环境可设为 True 查看 SQL 日志

    # 文件上传配置
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 单次上传上限 20MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'app', 'static', 'uploads')

    # 会话与登录
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 7  # 记住登录状态 7 天

    # 签到码有效期（秒），默认 10 分钟
    CHECKIN_CODE_EXPIRE = 10 * 60


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


# 配置字典，供应用工厂按环境名选择
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
