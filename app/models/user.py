# -*- coding: utf-8 -*-
"""用户模型（表：user）"""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db

# 角色常量
ROLE_STUDENT = 'student'       # 学生
ROLE_CLUB_ADMIN = 'admin_club'  # 社团管理员
ROLE_SYS_ADMIN = 'admin_sys'    # 系统管理员

ROLE_LABELS = {
    ROLE_STUDENT: '学生',
    ROLE_CLUB_ADMIN: '社团管理员',
    ROLE_SYS_ADMIN: '系统管理员',
}


class User(UserMixin, db.Model):
    """用户表
    字段设计依据项目说明书 5.2.1：
    id / username / password / real_name / student_id / email / phone
    / role / club_id / created_at / updated_at
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='密码（加密存储）')
    real_name = db.Column(db.String(50), comment='真实姓名')
    student_id = db.Column(db.String(20), comment='学号')
    email = db.Column(db.String(100), comment='邮箱')
    phone = db.Column(db.String(20), comment='手机号')
    role = db.Column(db.String(20), nullable=False, default=ROLE_STUDENT, comment='角色')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), comment='所属社团ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    club = db.relationship('Club', foreign_keys=[club_id], back_populates='members')
    registrations = db.relationship('Registration',
                                    foreign_keys='Registration.user_id',
                                    back_populates='user',
                                    cascade='all, delete-orphan', lazy='dynamic')
    checkins = db.relationship('Checkin', back_populates='user', lazy='dynamic')

    # ---- 密码处理 ----
    def set_password(self, raw_password: str) -> None:
        """加密存储密码（Werkzeug 加盐哈希）"""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """校验密码"""
        return check_password_hash(self.password, raw_password)

    # ---- 角色辅助 ----
    @property
    def is_student(self) -> bool:
        return self.role == ROLE_STUDENT

    @property
    def is_club_admin(self) -> bool:
        return self.role == ROLE_CLUB_ADMIN

    @property
    def is_sys_admin(self) -> bool:
        return self.role == ROLE_SYS_ADMIN

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)

    def has_role(self, *roles) -> bool:
        return self.role in roles

    def __repr__(self):
        return f'<User {self.username}>'
