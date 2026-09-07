# -*- coding: utf-8 -*-
"""
校园社团活动管理系统 —— 应用工厂
负责初始化扩展、注册蓝图、注册错误处理器与上下文处理器。
"""
import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config_map

# 全局扩展实例（应用工厂中初始化）
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录后再访问该页面。'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    """应用工厂：根据环境配置创建 Flask 应用"""
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # 确保上传目录存在
    _ensure_upload_dirs(app)

    # 用户加载器（Flask-Login）
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 注册蓝图
    _register_blueprints(app)

    # 注册错误处理
    _register_error_handlers(app)

    # 注册模板上下文处理器（全局注入角色常量、当前时间等）
    @app.context_processor
    def inject_globals():
        return {
            'ROLE_STUDENT': 'student',
            'ROLE_CLUB_ADMIN': 'admin_club',
            'ROLE_SYS_ADMIN': 'admin_sys',
        }

    # 首页与公共路由
    @app.route('/')
    def index():
        from app.services.activity_service import ActivityService
        data = ActivityService.get_index_page_data()
        return render_template('main/index.html', **data)

    return app


def _register_blueprints(app):
    """注册各功能模块蓝图"""
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.activity import bp as activity_bp
    from app.blueprints.registration import bp as registration_bp
    from app.blueprints.checkin import bp as checkin_bp
    from app.blueprints.archive import bp as archive_bp
    from app.blueprints.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(archive_bp)
    app.register_blueprint(admin_bp)


def _register_error_handlers(app):
    """自定义错误页面"""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def _ensure_upload_dirs(app):
    """确保上传目录存在"""
    for sub in ('covers', 'attachments'):
        path = os.path.join(app.config['UPLOAD_FOLDER'], sub)
        os.makedirs(path, exist_ok=True)
