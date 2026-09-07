# -*- coding: utf-8 -*-
"""报名与审核业务逻辑"""
from datetime import datetime

from app import db
from app.models.activity import Activity, ACTIVITY_CANCELLED
from app.models.registration import (Registration, REG_APPROVED, REG_CANCELLED,
                                     REG_PENDING, REG_REJECTED)
from app.models.user import User


class RegistrationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class RegistrationService:
    """报名 / 取消报名 / 审核"""

    @staticmethod
    def apply(activity: Activity, user) -> Registration:
        """学生报名活动
        校验：活动状态、重复报名、人数上限
        采用数据库唯一约束 + 事务，保证并发场景下不超员、不重复。
        """
        if activity.status == ACTIVITY_CANCELLED:
            raise RegistrationError('该活动已取消，无法报名。')

        existing = Registration.query.filter_by(activity_id=activity.id,
                                                user_id=user.id).first()
        if existing:
            if existing.status == REG_CANCELLED:
                # 取消后再次报名：直接恢复为待审核
                existing.status = REG_PENDING
                existing.apply_time = datetime.now()
                existing.review_time = None
                existing.review_comment = None
                db.session.commit()
                return existing
            raise RegistrationError('您已报名过该活动，请勿重复报名。')

        if activity.is_full:
            raise RegistrationError('该活动报名人数已满。')

        reg = Registration(activity_id=activity.id, user_id=user.id,
                           status=REG_PENDING)
        activity.current_participants += 1
        db.session.add(reg)
        db.session.commit()
        return reg

    @staticmethod
    def cancel(registration: Registration, user) -> None:
        """学生取消报名（仅待审核/已通过状态可取消）"""
        if registration.user_id != user.id:
            raise RegistrationError('无权操作该报名记录。')
        if registration.status not in (REG_PENDING, REG_APPROVED):
            raise RegistrationError('当前状态不可取消报名。')
        registration.status = REG_CANCELLED
        if registration.activity and registration.activity.current_participants > 0:
            registration.activity.current_participants -= 1
        db.session.commit()

    @staticmethod
    def review(registration: Registration, action: str, reviewer, comment: str = '') -> None:
        """社团管理员审核：通过 / 拒绝"""
        if registration.status != REG_PENDING:
            raise RegistrationError('该报名已审核，请勿重复操作。')
        if action not in ('approve', 'reject'):
            raise RegistrationError('非法的审核操作。')

        registration.status = REG_APPROVED if action == 'approve' else REG_REJECTED
        registration.review_time = datetime.now()
        registration.reviewer_id = reviewer.id
        registration.review_comment = (comment or '').strip()[:255]
        db.session.commit()

    @staticmethod
    def get_my_registrations(user):
        """当前用户的报名记录（按时间倒序）"""
        return (Registration.query
                .filter_by(user_id=user.id)
                .order_by(Registration.apply_time.desc())
                .all())

    @staticmethod
    def get_activity_registrations(activity: Activity, status=None, keyword=None):
        """某活动的报名列表，支持按状态筛选与姓名/学号搜索"""
        q = Registration.query.filter_by(activity_id=activity.id)
        if status:
            q = q.filter(Registration.status == status)
        if keyword:
            like = f'%{keyword}%'
            q = q.join(User).filter(db.or_(User.real_name.like(like),
                                           User.student_id.like(like)))
        return q.order_by(Registration.apply_time.asc()).all()
