# -*- coding: utf-8 -*-
"""活动业务逻辑"""
from datetime import datetime

from flask import current_app
from flask_login import current_user

from app import db
from app.models.activity import (Activity, ACTIVITY_ENDED, ACTIVITY_CANCELLED,
                                 ACTIVITY_STATUS_LABELS)
from app.models.club import Club
from app.models.user import User


class ActivityError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ActivityService:
    """活动发布、编辑、删除、状态管理、查询"""

    # ---- 创建 / 编辑 ----
    @staticmethod
    def _validate_times(start_time, end_time):
        if not start_time or not end_time:
            raise ActivityError('开始时间与结束时间均不能为空。')
        if start_time >= end_time:
            raise ActivityError('开始时间不能晚于或等于结束时间。')

    @staticmethod
    def _validate_max(max_participants):
        if max_participants is not None and max_participants <= 0:
            raise ActivityError('最大参与人数必须为正整数。')

    @classmethod
    def create_activity(cls, club_id, title, description, location,
                        start_time, end_time, max_participants,
                        cover_image=None) -> Activity:
        title = (title or '').strip()
        if not title:
            raise ActivityError('活动标题不能为空。')
        cls._validate_times(start_time, end_time)
        cls._validate_max(max_participants)

        activity = Activity(
            club_id=club_id,
            title=title,
            description=description or '',
            location=(location or '').strip(),
            cover_image=cover_image,
            start_time=start_time,
            end_time=end_time,
            max_participants=max_participants,
            publisher_id=current_user.id,
            status='pending',  # 初始为待发布
        )
        db.session.add(activity)
        db.session.commit()
        return activity

    @classmethod
    def update_activity(cls, activity: Activity, title, description, location,
                        start_time, end_time, max_participants,
                        cover_image=None) -> None:
        title = (title or '').strip()
        if not title:
            raise ActivityError('活动标题不能为空。')
        cls._validate_times(start_time, end_time)
        cls._validate_max(max_participants)

        activity.title = title
        activity.description = description or ''
        activity.location = (location or '').strip()
        activity.start_time = start_time
        activity.end_time = end_time
        activity.max_participants = max_participants
        if cover_image:
            activity.cover_image = cover_image
        db.session.commit()

    @staticmethod
    def delete_activity(activity: Activity) -> None:
        """删除活动（连同报名、签到、归档级联删除）"""
        db.session.delete(activity)
        db.session.commit()

    @staticmethod
    def set_status(activity: Activity, status: str) -> None:
        if status not in ACTIVITY_STATUS_LABELS:
            raise ActivityError('非法的活动状态。')
        activity.status = status
        db.session.commit()

    # ---- 查询 ----
    @staticmethod
    def get_visible_activities(club_id=None, keyword=None, status=None,
                               order='newest'):
        """活动列表查询（支持按社团、关键词、状态筛选）"""
        q = Activity.query
        if club_id:
            q = q.filter(Activity.club_id == club_id)
        if status:
            q = q.filter(Activity.status == status)
        if keyword:
            like = f'%{keyword}%'
            q = q.filter(db.or_(Activity.title.like(like),
                                Activity.location.like(like),
                                Activity.description.like(like)))
        if order == 'upcoming':
            q = q.order_by(Activity.start_time.asc())
        else:
            q = q.order_by(Activity.created_at.desc())
        return q.all()

    @staticmethod
    def get_clubs():
        return Club.query.filter_by(status='active').order_by(Club.name).all()

    @staticmethod
    def get_index_page_data():
        """首页聚合数据：推荐进行中/即将开始的活动、近期活动、热门社团"""
        now = datetime.now()
        featured = (Activity.query
                    .filter(Activity.status.in_(['ongoing', 'pending']),
                            Activity.end_time >= now)
                    .order_by(Activity.start_time.asc()).limit(6).all())
        recent = Activity.query.order_by(Activity.created_at.desc()).limit(6).all()
        clubs = Club.query.filter_by(status='active').order_by(Club.created_at.desc()).limit(6).all()
        return {
            'featured_activities': featured,
            'recent_activities': recent,
            'clubs': clubs,
            'total_activities': Activity.query.count(),
            'total_clubs': Club.query.count(),
            'total_users': User.query.count(),
        }

    @staticmethod
    def can_manage(activity: Activity, user: User) -> bool:
        """判断用户是否有权管理该活动（本社团管理员 或 系统管理员）"""
        if user.is_sys_admin:
            return True
        return user.is_club_admin and user.club_id == activity.club_id
