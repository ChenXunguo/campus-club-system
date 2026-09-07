# -*- coding: utf-8 -*-
"""活动模型（表：activity）"""
from datetime import datetime

from app import db

# 活动状态常量
ACTIVITY_PENDING = 'pending'     # 待发布
ACTIVITY_ONGOING = 'ongoing'     # 进行中
ACTIVITY_ENDED = 'ended'         # 已结束
ACTIVITY_CANCELLED = 'cancelled'  # 已取消

ACTIVITY_STATUS_LABELS = {
    ACTIVITY_PENDING: '待发布',
    ACTIVITY_ONGOING: '进行中',
    ACTIVITY_ENDED: '已结束',
    ACTIVITY_CANCELLED: '已取消',
}


class Activity(db.Model):
    """活动表
    字段设计依据项目说明书 5.2.3：
    id / club_id / title / description / cover_image / location / start_time
    / end_time / max_participants / current_participants / status
    / publisher_id / created_at / updated_at
    扩展字段（为签到二维码功能服务，见 README）：
    checkin_code / checkin_expire —— 活动级签到码及其有效期
    """
    __tablename__ = 'activity'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='活动ID')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False, comment='所属社团ID')
    title = db.Column(db.String(200), nullable=False, comment='活动标题')
    description = db.Column(db.Text, comment='活动详情（富文本）')
    cover_image = db.Column(db.String(255), comment='封面图片路径')
    location = db.Column(db.String(255), comment='活动地点')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=False, comment='结束时间')
    max_participants = db.Column(db.Integer, comment='最大参与人数')
    current_participants = db.Column(db.Integer, default=0, comment='当前报名人数')
    status = db.Column(db.String(20), default=ACTIVITY_PENDING, comment='活动状态')
    publisher_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='发布人ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 扩展：签到码（二维码功能）
    checkin_code = db.Column(db.String(100), comment='当前签到码')
    checkin_expire = db.Column(db.DateTime, comment='签到码有效期至')

    # 关系
    club = db.relationship('Club', back_populates='activities')
    publisher = db.relationship('User', foreign_keys=[publisher_id])
    registrations = db.relationship('Registration', back_populates='activity',
                                    lazy='dynamic', cascade='all, delete-orphan')
    checkins = db.relationship('Checkin', back_populates='activity', lazy='dynamic')
    archive = db.relationship('Archive', back_populates='activity',
                              uselist=False, cascade='all, delete-orphan')

    # ---- 状态辅助 ----
    @property
    def status_label(self) -> str:
        return ACTIVITY_STATUS_LABELS.get(self.status, self.status)

    @property
    def is_full(self) -> bool:
        """是否报满"""
        return self.max_participants is not None and self.current_participants >= self.max_participants

    @property
    def participant_slots(self) -> str:
        return f'{self.current_participants}/{self.max_participants if self.max_participants else "不限"}'

    # ---- 签到统计 ----
    @property
    def approved_count(self) -> int:
        """报名通过人数"""
        return self.registrations.filter_by(status='approved').count()

    @property
    def checked_in_count(self) -> int:
        """已签到人数"""
        return self.checkins.count()

    @property
    def checkin_rate(self):
        """签到率 = 已签到人数 / 报名通过人数 × 100%
        说明：若报名通过人数为 0 且无人签到，视为 0%；若报名通过 0 但有签到，视为 100%。
        """
        approved = self.approved_count
        checked = self.checked_in_count
        if approved <= 0:
            return 100.0 if checked > 0 else 0.0
        return round(checked / approved * 100, 1)

    def __repr__(self):
        return f'<Activity {self.title}>'
