# -*- coding: utf-8 -*-
"""活动模块蓝图：活动列表、详情（公共浏览）"""
from flask import (Blueprint, abort, render_template, request)
from flask_login import current_user

from app import db
from app.models.activity import Activity
from app.models.registration import Registration
from app.services.activity_service import ActivityService

bp = Blueprint('activity', __name__)


def _request_arg(key):
    return request.args.get(key, '').strip()


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@bp.route('/activities')
def list_activities():
    """活动列表页：支持按社团、关键词、状态筛选"""
    club_id = _to_int(_request_arg('club_id'))
    keyword = _request_arg('keyword')
    status = _request_arg('status')

    activities = ActivityService.get_visible_activities(
        club_id=club_id, keyword=keyword, status=status)
    clubs = ActivityService.get_clubs()

    return render_template('activity/list.html',
                           activities=activities,
                           clubs=clubs,
                           filters={'club_id': club_id, 'keyword': keyword,
                                    'status': status})


@bp.route('/activity/<int:activity_id>')
def detail(activity_id):
    """活动详情页"""
    activity = db.session.get(Activity, activity_id)
    if not activity:
        abort(404)

    # 当前登录用户是否已报名 / 已签到
    my_registration = None
    my_checkin = None
    if current_user.is_authenticated:
        my_registration = Registration.query.filter_by(
            activity_id=activity.id, user_id=current_user.id).first()
        if my_registration and my_registration.status == 'approved':
            my_checkin = activity.checkins.filter_by(
                user_id=current_user.id).first()

    return render_template('activity/detail.html',
                           activity=activity,
                           my_registration=my_registration,
                           my_checkin=my_checkin)
