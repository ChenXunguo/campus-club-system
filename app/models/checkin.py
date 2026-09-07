# -*- coding: utf-8 -*-
"""签到模型（表：checkin）"""
from datetime import datetime

from app import db

# 签到类型
CHECKIN_TYPE_QR = 'qr'         # 二维码扫码签到
CHECKIN_TYPE_MANUAL = 'manual' # 管理员手动签到

# 签到状态
CHECKIN_SUCCESS = 'success'
CHECKIN_FAILED = 'failed'


class Checkin(db.Model):
    """签到表
    字段设计依据项目说明书 5.2.5：
    id / registration_id / activity_id / user_id / checkin_time
    / checkin_code / checkin_type / status
    """
    __tablename__ = 'checkin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='签到ID')
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'),
                                nullable=False, comment='报名记录ID')
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'),
                            nullable=False, comment='活动ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False, comment='签到用户ID')
    checkin_time = db.Column(db.DateTime, default=datetime.now, comment='签到时间')
    checkin_code = db.Column(db.String(100), comment='签到码')
    checkin_type = db.Column(db.String(20), default=CHECKIN_TYPE_QR, comment='签到方式')
    status = db.Column(db.String(20), default=CHECKIN_SUCCESS, comment='状态：success/failed')

    # 关系
    registration = db.relationship('Registration', back_populates='checkin')
    activity = db.relationship('Activity', back_populates='checkins')
    user = db.relationship('User', back_populates='checkins')

    @property
    def checkin_type_label(self) -> str:
        return '扫码签到' if self.checkin_type == CHECKIN_TYPE_QR else '手动签到'

    @property
    def status_label(self) -> str:
        return '成功' if self.status == CHECKIN_SUCCESS else '失败'

    def __repr__(self):
        return f'<Checkin activity={self.activity_id} user={self.user_id}>'
