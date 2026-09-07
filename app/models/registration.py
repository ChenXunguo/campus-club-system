# -*- coding: utf-8 -*-
"""报名模型（表：registration）"""
from datetime import datetime

from app import db

# 报名状态常量
REG_PENDING = 'pending'    # 待审核
REG_APPROVED = 'approved'  # 已通过
REG_REJECTED = 'rejected'  # 已拒绝
REG_CANCELLED = 'cancelled'  # 已取消（学生主动取消）

REG_STATUS_LABELS = {
    REG_PENDING: '待审核',
    REG_APPROVED: '已通过',
    REG_REJECTED: '已拒绝',
    REG_CANCELLED: '已取消',
}


class Registration(db.Model):
    """报名表
    字段设计依据项目说明书 5.2.4：
    id / activity_id / user_id / status / apply_time / review_time
    / reviewer_id / review_comment
    附加唯一约束 (activity_id, user_id) 实现防重复报名。
    """
    __tablename__ = 'registration'
    __table_args__ = (
        # 防重复报名：同一用户对同一活动只能有一条报名记录
        db.UniqueConstraint('activity_id', 'user_id', name='uk_activity_user'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='报名ID')
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'),
                            nullable=False, comment='活动ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False, comment='报名用户ID')
    status = db.Column(db.String(20), default=REG_PENDING, comment='报名状态')
    apply_time = db.Column(db.DateTime, default=datetime.now, comment='报名时间')
    review_time = db.Column(db.DateTime, comment='审核时间')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审核人ID')
    review_comment = db.Column(db.String(255), comment='审核备注')

    # 关系
    activity = db.relationship('Activity', back_populates='registrations')
    user = db.relationship('User', foreign_keys=[user_id],
                           back_populates='registrations')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    checkin = db.relationship('Checkin', back_populates='registration',
                              uselist=False, cascade='all, delete-orphan')

    @property
    def status_label(self) -> str:
        return REG_STATUS_LABELS.get(self.status, self.status)

    def __repr__(self):
        return f'<Registration activity={self.activity_id} user={self.user_id}>'
