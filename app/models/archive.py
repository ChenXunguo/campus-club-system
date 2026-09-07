# -*- coding: utf-8 -*-
"""总结归档模型（表：archive）"""
from datetime import datetime

from app import db


class Archive(db.Model):
    """总结归档表
    字段设计依据项目说明书 5.2.6：
    id / activity_id / summary / attachment_path / semester
    / archive_time / archiver_id / is_archived
    """
    __tablename__ = 'archive'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='归档ID')
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'),
                            unique=True, nullable=False, comment='活动ID（一对一）')
    summary = db.Column(db.Text, comment='活动总结')
    attachment_path = db.Column(db.String(255), comment='附件路径')
    semester = db.Column(db.String(20), comment='学期（如2026-2027-1）')
    archive_time = db.Column(db.DateTime, default=datetime.now, comment='归档时间')
    archiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='归档人ID')
    is_archived = db.Column(db.Boolean, default=False, comment='是否已归档')

    # 关系
    activity = db.relationship('Activity', back_populates='archive')
    archiver = db.relationship('User', foreign_keys=[archiver_id])

    def __repr__(self):
        return f'<Archive activity={self.activity_id}>'
