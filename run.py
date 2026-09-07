# -*- coding: utf-8 -*-
"""项目启动文件"""
import os

from app import create_app

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))


if __name__ == '__main__':
    # 默认 0.0.0.0:5000，局域网内可通过本机 IP 访问（便于手机扫码签到测试）
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=app.config.get('DEBUG', False))
