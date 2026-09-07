# -*- coding: utf-8 -*-
"""报名模块蓝图：报名 / 取消报名 / 我的报名"""
from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.models.activity import Activity
from app.models.registration import Registration
from app.services.registration_service import (RegistrationError,
                                               RegistrationService)

bp = Blueprint('registration', __name__)


@bp.route('/activity/<int:activity_id>/register', methods=['POST'])
@login_required
def apply(activity_id):
    """学生报名活动"""
    if current_user.is_club_admin or current_user.is_sys_admin:
        flash('管理员账号无需报名活动。', 'warning')
        return redirect(url_for('activity.detail', activity_id=activity_id))

    activity = db.session.get(Activity, activity_id)
    if not activity:
        abort(404)
    try:
        RegistrationService.apply(activity, current_user)
    except RegistrationError as e:
        flash(e.message, 'danger')
    else:
        flash('报名成功，等待社团管理员审核。', 'success')
    return redirect(url_for('activity.detail', activity_id=activity_id))


@bp.route('/registration/<int:reg_id>/cancel', methods=['POST'])
@login_required
def cancel(reg_id):
    """学生取消报名"""
    registration = db.session.get(Registration, reg_id)
    if not registration:
        abort(404)
    try:
        RegistrationService.cancel(registration, current_user)
    except RegistrationError as e:
        flash(e.message, 'danger')
    else:
        flash('已取消报名。', 'info')
    return redirect(request.referrer or url_for('registration.my_registrations'))


@bp.route('/my-registrations')
@login_required
def my_registrations():
    """我的报名"""
    registrations = RegistrationService.get_my_registrations(current_user)
    return render_template('registration/my_registrations.html',
                           registrations=registrations)
