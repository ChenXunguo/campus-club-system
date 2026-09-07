# -*- coding: utf-8 -*-
"""认证与用户业务逻辑"""
from app import db
from app.models.user import User, ROLE_STUDENT


class AuthError(Exception):
    """业务异常：携带可展示给用户的错误信息"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class AuthService:
    """用户注册 / 登录 / 资料维护"""

    @staticmethod
    def register(username: str, password: str, real_name: str = '',
                 student_id: str = '', email: str = '', phone: str = '') -> User:
        """注册新用户（默认角色：学生）"""
        username = (username or '').strip()
        if len(username) < 3:
            raise AuthError('用户名长度不能少于 3 个字符。')
        if len(password) < 6:
            raise AuthError('密码长度不能少于 6 个字符。')

        if User.query.filter_by(username=username).first():
            raise AuthError('该用户名已被注册。')

        user = User(
            username=username,
            real_name=(real_name or '').strip(),
            student_id=(student_id or '').strip(),
            email=(email or '').strip(),
            phone=(phone or '').strip(),
            role=ROLE_STUDENT,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(username: str, password: str) -> User:
        """校验用户名密码，成功返回用户，失败抛出 AuthError"""
        user = User.query.filter_by(username=(username or '').strip()).first()
        if not user or not user.check_password(password or ''):
            raise AuthError('用户名或密码错误。')
        return user

    @staticmethod
    def update_profile(user: User, real_name=None, student_id=None,
                       email=None, phone=None, old_password=None, new_password=None) -> None:
        """更新个人信息（支持修改密码）"""
        if real_name is not None:
            user.real_name = (real_name or '').strip()
        if student_id is not None:
            user.student_id = (student_id or '').strip()
        if email is not None:
            user.email = (email or '').strip()
        if phone is not None:
            user.phone = (phone or '').strip()

        # 修改密码：需校验旧密码
        if new_password:
            if len(new_password) < 6:
                raise AuthError('新密码长度不能少于 6 个字符。')
            if not user.check_password(old_password or ''):
                raise AuthError('原密码错误。')
            user.set_password(new_password)

        db.session.commit()
