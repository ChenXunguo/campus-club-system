# -*- coding: utf-8 -*-
"""认证模块蓝图：注册 / 登录 / 登出 / 个人信息"""
from flask import (Blueprint, flash, redirect, render_template, request, url_for)
from flask_login import (current_user, login_required, login_user, logout_user)

from app.models.user import User
from app.services.auth_service import AuthError, AuthService

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册（默认学生角色）"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            user = AuthService.register(
                username=request.form.get('username', ''),
                password=request.form.get('password', ''),
                real_name=request.form.get('real_name', ''),
                student_id=request.form.get('student_id', ''),
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
            )
        except AuthError as e:
            flash(e.message, 'danger')
            return render_template('auth/register.html',
                                   form=request.form)
        flash('注册成功，请登录。', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        try:
            user = AuthService.authenticate(username, password)
        except AuthError as e:
            flash(e.message, 'danger')
            return render_template('auth/login.html', username=username)

        login_user(user, remember=remember)
        flash(f'欢迎回来，{user.username}！', 'success')
        next_url = request.args.get('next')
        # 防止开放重定向
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
        return redirect(url_for('index'))
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已安全退出登录。', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人信息管理"""
    if request.method == 'POST':
        try:
            AuthService.update_profile(
                user=current_user,
                real_name=request.form.get('real_name', ''),
                student_id=request.form.get('student_id', ''),
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                old_password=request.form.get('old_password') or None,
                new_password=request.form.get('new_password') or None,
            )
        except AuthError as e:
            flash(e.message, 'danger')
            return render_template('auth/profile.html')
        flash('个人信息已更新。', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html')
