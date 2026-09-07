@echo off
chcp 65001 >nul
title 校园社团活动管理系统
echo ============================================
echo    校园社团活动管理系统 - 启动脚本
echo ============================================
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
    echo [提示] 未找到虚拟环境，正在创建并安装依赖...
    python -m venv venv
    venv\Scripts\python -m pip install -r requirements.txt
)

echo [1/2] 检查并初始化数据库...
venv\Scripts\python scripts\init_db.py

echo [2/2] 启动服务（浏览器访问 http://127.0.0.1:5000）...
venv\Scripts\python run.py

pause
