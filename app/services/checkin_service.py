# -*- coding: utf-8 -*-
"""签到业务逻辑：二维码生成、扫码签到、签到统计"""
import base64
import io
import secrets
from datetime import datetime, timedelta

import qrcode
from flask import current_app, request, url_for

from app import db
from app.models.activity import Activity, ACTIVITY_ENDED, ACTIVITY_CANCELLED
from app.models.checkin import (Checkin, CHECKIN_SUCCESS, CHECKIN_TYPE_MANUAL,
                                CHECKIN_TYPE_QR)
from app.models.registration import Registration, REG_APPROVED


class CheckinError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class CheckinService:
    """签到码生成 / 扫码签到 / 手动签到 / 统计导出"""

    @staticmethod
    def generate_code(activity: Activity) -> str:
        """为活动生成唯一签到码（带有效期），返回签到码字符串"""
        code = secrets.token_urlsafe(16)
        activity.checkin_code = code
        activity.checkin_expire = datetime.now() + timedelta(
            seconds=current_app.config.get('CHECKIN_CODE_EXPIRE', 600))
        db.session.commit()
        return code

    @staticmethod
    def is_code_valid(activity: Activity, code: str) -> bool:
        """校验签到码是否存在且未过期"""
        if not activity.checkin_code or not code:
            return False
        if secrets.compare_digest(activity.checkin_code, code) is False:
            return False
        if activity.checkin_expire and datetime.now() > activity.checkin_expire:
            return False
        return True

    @staticmethod
    def qr_data_uri(activity: Activity, code: str) -> str:
        """生成签到二维码（内容为签到 URL）的 base64 图片"""
        url = url_for('checkin.scan', activity_id=activity.id, code=code,
                      _external=True)
        img = qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        data = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f'data:image/png;base64,{data}'

    @staticmethod
    def scan_checkin(activity: Activity, code: str, user):
        """扫码签到（二维码方式）
        校验顺序：活动状态 → 签到码有效性 → 是否已签到 → 是否报名且审核通过
        """
        # 1. 活动状态
        if activity.status == ACTIVITY_CANCELLED:
            raise CheckinError('该活动已取消，无法签到。')
        if activity.status == ACTIVITY_ENDED:
            raise CheckinError('该活动已结束，无法签到。')

        # 2. 签到码有效性
        if not CheckinService.is_code_valid(activity, code):
            raise CheckinError('签到码已失效，请联系社团管理员重新生成。')

        # 3. 是否已签到
        if Checkin.query.filter_by(activity_id=activity.id, user_id=user.id,
                                   status=CHECKIN_SUCCESS).first():
            raise CheckinError('您已完成签到，无需重复操作。')

        # 4. 是否报名且审核通过
        registration = Registration.query.filter_by(activity_id=activity.id,
                                                    user_id=user.id).first()
        if not registration:
            raise CheckinError('您未报名该活动，无法签到。')
        if registration.status != REG_APPROVED:
            # 记录一条失败签到（复用其报名记录）
            db.session.add(Checkin(
                registration_id=registration.id,
                activity_id=activity.id,
                user_id=user.id,
                checkin_code=code,
                checkin_type=CHECKIN_TYPE_QR,
                status='failed',
            ))
            db.session.commit()
            raise CheckinError('您报名未通过审核，无法签到。')

        # 5. 写入签到记录
        checkin = Checkin(
            registration_id=registration.id,
            activity_id=activity.id,
            user_id=user.id,
            checkin_code=code,
            checkin_type=CHECKIN_TYPE_QR,
            status=CHECKIN_SUCCESS,
        )
        db.session.add(checkin)
        db.session.commit()
        return checkin

    @staticmethod
    def manual_checkin(activity: Activity, registration: Registration) -> Checkin:
        """管理员手动签到（补签）"""
        if Checkin.query.filter_by(activity_id=activity.id,
                                   user_id=registration.user_id,
                                   status=CHECKIN_SUCCESS).first():
            raise CheckinError('该用户已完成签到。')
        checkin = Checkin(
            registration_id=registration.id,
            activity_id=activity.id,
            user_id=registration.user_id,
            checkin_code=activity.checkin_code or 'manual',
            checkin_type=CHECKIN_TYPE_MANUAL,
            status=CHECKIN_SUCCESS,
        )
        db.session.add(checkin)
        db.session.commit()
        return checkin

    @staticmethod
    def get_activity_checkins(activity: Activity):
        """活动签到记录"""
        return (Checkin.query
                .filter_by(activity_id=activity.id)
                .order_by(Checkin.checkin_time.asc())
                .all())

    @staticmethod
    def get_my_checkins(user):
        """当前用户的签到记录"""
        return (Checkin.query
                .filter_by(user_id=user.id)
                .order_by(Checkin.checkin_time.desc())
                .all())

    @staticmethod
    def activity_stats(activity: Activity):
        """活动签到统计信息"""
        approved = activity.approved_count
        checked = activity.checked_in_count
        return {
            'approved': approved,
            'checked': checked,
            'unchecked': max(approved - checked, 0),
            'rate': activity.checkin_rate,
        }
