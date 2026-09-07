# -*- coding: utf-8 -*-
"""pytest 夹具：使用独立测试数据库 club_system_test
注意：Flask-Login 将登录用户缓存在 `g`（应用上下文级全局）。
若用单个 app_context 包裹整个测试会话，会把上一测试的登录状态泄漏到下一测试。
因此每个测试通过 client fixture 进入独立 app_context。
"""
import os
import sys

# 必须在导入 Config 之前设置测试库名，确保配置读取到测试库
TEST_DB = 'club_system_test'
os.environ['DB_NAME'] = TEST_DB

import pymysql  # noqa: E402
import pytest  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402


@pytest.fixture(scope='session')
def app():
    """创建测试应用（独立测试库），会话级：仅负责建库、建表、种子"""
    conn = pymysql.connect(host=Config.DB_HOST, port=int(Config.DB_PORT),
                           user=Config.DB_USERNAME, password=Config.DB_PASSWORD,
                           charset='utf8mb4')
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS `{TEST_DB}`')
            cur.execute(f'CREATE DATABASE `{TEST_DB}` DEFAULT CHARACTER SET '
                        f'utf8mb4 COLLATE utf8mb4_unicode_ci')
        conn.commit()
    finally:
        conn.close()

    from app import create_app, db
    application = create_app('testing')
    with application.app_context():
        db.create_all()
        _seed_base()

    yield application

    # 清理：club↔user 存在循环外键，采用原生 SQL 关闭外键检查后删除
    with application.app_context():
        with db.engine.begin() as conn:
            conn.execute(db.text('SET FOREIGN_KEY_CHECKS = 0'))
            for t in ('checkin', 'archive', 'registration',
                      'activity', 'user', 'club'):
                conn.execute(db.text(f'DROP TABLE IF EXISTS `{t}`'))
            conn.execute(db.text('SET FOREIGN_KEY_CHECKS = 1'))
    os.environ.pop('DB_NAME', None)


@pytest.fixture
def client(app):
    """每个测试进入独立应用上下文，避免 g._login_user 跨测试泄漏"""
    with app.app_context():
        yield app.test_client()


def _seed_base():
    """写入测试基础数据"""
    from app import db
    from app.models.club import Club
    from app.models.user import User, ROLE_CLUB_ADMIN, ROLE_SYS_ADMIN

    admin = User(username='admin', real_name='管理员', role=ROLE_SYS_ADMIN)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()  # 获取 admin.id

    club = Club(name='测试篮球社', category='文体类',
                description='测试社团', founder_id=admin.id)
    db.session.add(club)
    db.session.flush()

    club_admin = User(username='clubadmin', real_name='社团管理',
                      role=ROLE_CLUB_ADMIN, club_id=club.id)
    club_admin.set_password('123456')
    db.session.add(club_admin)

    student = User(username='student1', real_name='张三', student_id='20230001')
    student.set_password('123456')
    db.session.add(student)

    student2 = User(username='student2', real_name='李四', student_id='20230002')
    student2.set_password('123456')
    db.session.add(student2)
    db.session.commit()


@pytest.fixture
def login_helpers():
    """登录辅助函数"""
    def login(client, username, password):
        return client.post('/login', data={'username': username,
                                           'password': password},
                           follow_redirects=True)

    def logout(client):
        return client.get('/logout', follow_redirects=True)
    return {'login': login, 'logout': logout}
