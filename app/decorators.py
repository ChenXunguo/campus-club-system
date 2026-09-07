# -*- coding: utf-8 -*-
"""
自定义权限装饰器
依据说明书 7.2.5：装饰器执行顺序 @login_required → @role_required
"""
from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def role_required(*roles):
    """
    角色访问控制装饰器：仅允许指定角色的用户访问。
    用法：@role_required('admin_club', 'admin_sys')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 未登录：交由 Flask-Login 的 login_view 处理
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            # 已登录但角色不符：返回 403 Forbidden
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def club_admin_or_sys_required(f):
    """社团管理员或系统管理员可访问"""
    return role_required('admin_club', 'admin_sys')(f)


def sys_admin_required(f):
    """仅系统管理员可访问"""
    return role_required('admin_sys')(f)
