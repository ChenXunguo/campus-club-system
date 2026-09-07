# -*- coding: utf-8 -*-
"""社团模型（表：club）"""
from datetime import datetime

from app import db


class Club(db.Model):
    """社团表
    字段设计依据项目说明书 5.2.2：
    id / name / description / category / founder_id / created_at / status
    """
    __tablename__ = 'club'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='社团ID')
    name = db.Column(db.String(80), unique=True, nullable=False, comment='社团名称')
    description = db.Column(db.Text, comment='社团简介')
    category = db.Column(db.String(50), comment='社团类别')
    founder_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创始人ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    status = db.Column(db.String(20), default='active', comment='状态：active/inactive')

    # 关系
    founder = db.relationship('User', foreign_keys=[founder_id])
    members = db.relationship('User', foreign_keys='User.club_id',
                              back_populates='club', lazy='dynamic')
    activities = db.relationship('Activity', back_populates='club',
                                 lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_active(self) -> bool:
        return self.status == 'active'

    @property
    def member_count(self) -> int:
        return self.members.count()

    @property
    def activity_count(self) -> int:
        return self.activities.count()

    def __repr__(self):
        return f'<Club {self.name}>'
