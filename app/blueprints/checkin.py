# -*- coding: utf-8 -*-
"""签到模块蓝图：扫码签到、我的签到记录"""
from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.models.activity import Activity
from app.services.checkin_service import CheckinError, CheckinService

bp = Blueprint('checkin', __name__)


@bp.route('/checkin/<int:activity_id>')
@login_required
def scan(activity_id):
    """扫码签到入口
    二维码内容指向本路由（携带 code 参数），手机扫码即触发签到。
    """
    activity = db.session.get(Activity, activity_id)
    if not activity:
        abort(404)
    code = request.args.get('code', '')
    try:
        CheckinService.scan_checkin(activity, code, current_user)
    except CheckinError as e:
        flash(e.message, 'danger')
    else:
        flash(f'签到成功！活动：{activity.title}', 'success')
    return redirect(url_for('activity.detail', activity_id=activity.id))


@bp.route('/my-checkins')
@login_required
def my_checkins():
    """我的签到记录"""
    checkins = CheckinService.get_my_checkins(current_user)
    return render_template('checkin/my_checkins.html', checkins=checkins)
