# -*- coding: utf-8 -*-
"""管理模块蓝图（按说明书 6.1 页面结构）：
社团管理员端：活动管理 / 报名审核 / 签到管理 / 总结上传 / 归档管理
系统管理员端：用户管理 / 社团管理 / 权限分配
"""
import csv
import io
from datetime import datetime

from flask import (Blueprint, abort, current_app, flash,
                   redirect, render_template, request, send_file, url_for)
from flask_login import current_user, login_required

from app import db
from app.decorators import club_admin_or_sys_required, sys_admin_required
from app.models.activity import Activity
from app.models.archive import Archive
from app.models.checkin import Checkin
from app.models.club import Club
from app.models.registration import Registration
from app.models.user import User, ROLE_CLUB_ADMIN, ROLE_STUDENT, ROLE_SYS_ADMIN
from app.services.activity_service import ActivityError, ActivityService
from app.services.archive_service import ArchiveError, ArchiveService
from app.services.checkin_service import CheckinError, CheckinService
from app.services.club_service import ClubError, ClubService
from app.services.registration_service import (RegistrationError,
                                               RegistrationService)
from app.utils import save_attachment, save_cover

bp = Blueprint('admin', __name__)


# ============================================================
# 公共辅助
# ============================================================
def _manageable_activities():
    """当前管理员可管理的活动：本社团管理员只能看本社团活动，系统管理员可看全部"""
    if current_user.is_sys_admin:
        return Activity.query.order_by(Activity.created_at.desc()).all()
    return (Activity.query
            .filter_by(club_id=current_user.club_id)
            .order_by(Activity.created_at.desc())
            .all())


def _get_manageable_activity(activity_id) -> Activity:
    """校验当前用户是否有权管理指定活动，无权则 404/403"""
    activity = db.session.get(Activity, activity_id)
    if not activity:
        abort(404)
    if not ActivityService.can_manage(activity, current_user):
        abort(403)
    return activity


def _parse_dt(value):
    """解析表单 datetime-local 字符串"""
    if not value:
        return None
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


# ============================================================
# 活动管理（社团管理员 / 系统管理员）
# ============================================================
@bp.route('/admin/activities')
@club_admin_or_sys_required
def activity_list():
    """活动管理列表"""
    status = request.args.get('status', '').strip()
    activities = _manageable_activities()
    if status:
        activities = [a for a in activities if a.status == status]
    return render_template('admin/activity_list.html', activities=activities,
                           status=status)


@bp.route('/admin/activity/create', methods=['GET', 'POST'])
@club_admin_or_sys_required
def activity_create():
    """发布活动"""
    clubs = Club.query.filter_by(status='active').all()
    if not clubs:
        flash('当前没有可用的社团，请先联系系统管理员创建社团。', 'warning')

    if request.method == 'POST':
        try:
            cover = save_cover(request.files.get('cover_image'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('admin/activity_form.html', clubs=clubs,
                                   activity=None, form=request.form)

        club_id = request.form.get('club_id', type=int)
        # 社团管理员只能为自己的社团发布活动
        if current_user.is_club_admin and club_id != current_user.club_id:
            flash('社团管理员只能为本社团发布活动。', 'danger')
            return render_template('admin/activity_form.html', clubs=clubs,
                                   activity=None, form=request.form)

        try:
            activity = ActivityService.create_activity(
                club_id=club_id,
                title=request.form.get('title', ''),
                description=request.form.get('description', ''),
                location=request.form.get('location', ''),
                start_time=_parse_dt(request.form.get('start_time')),
                end_time=_parse_dt(request.form.get('end_time')),
                max_participants=request.form.get('max_participants', type=int),
                cover_image=cover or None,
            )
        except ActivityError as e:
            flash(e.message, 'danger')
            return render_template('admin/activity_form.html', clubs=clubs,
                                   activity=None, form=request.form)

        flash('活动发布成功（初始状态：待发布）。', 'success')
        return redirect(url_for('admin.activity_list'))

    return render_template('admin/activity_form.html', clubs=clubs,
                           activity=None, form={})


@bp.route('/admin/activity/<int:activity_id>/edit', methods=['GET', 'POST'])
@club_admin_or_sys_required
def activity_edit(activity_id):
    """编辑活动"""
    activity = _get_manageable_activity(activity_id)
    clubs = Club.query.filter_by(status='active').all()

    if request.method == 'POST':
        try:
            cover = save_cover(request.files.get('cover_image'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('admin/activity_form.html', clubs=clubs,
                                   activity=activity, form=request.form)
        try:
            ActivityService.update_activity(
                activity=activity,
                title=request.form.get('title', ''),
                description=request.form.get('description', ''),
                location=request.form.get('location', ''),
                start_time=_parse_dt(request.form.get('start_time')),
                end_time=_parse_dt(request.form.get('end_time')),
                max_participants=request.form.get('max_participants', type=int),
                cover_image=cover or None,
            )
        except ActivityError as e:
            flash(e.message, 'danger')
            return render_template('admin/activity_form.html', clubs=clubs,
                                   activity=activity, form=request.form)
        flash('活动信息已更新。', 'success')
        return redirect(url_for('admin.activity_list'))
    return render_template('admin/activity_form.html', clubs=clubs,
                           activity=activity, form={})


@bp.route('/admin/activity/<int:activity_id>/delete', methods=['POST'])
@club_admin_or_sys_required
def activity_delete(activity_id):
    """删除活动"""
    activity = _get_manageable_activity(activity_id)
    title = activity.title
    ActivityService.delete_activity(activity)
    flash(f'活动「{title}」已删除。', 'info')
    return redirect(url_for('admin.activity_list'))


@bp.route('/admin/activity/<int:activity_id>/status', methods=['POST'])
@club_admin_or_sys_required
def activity_status(activity_id):
    """活动状态管理：待发布/进行中/已结束/已取消"""
    activity = _get_manageable_activity(activity_id)
    status = request.form.get('status', '')
    try:
        ActivityService.set_status(activity, status)
    except ActivityError as e:
        flash(e.message, 'danger')
    else:
        flash(f'活动状态已更新为：{activity.status_label}。', 'success')
    return redirect(url_for('admin.activity_list'))


# ============================================================
# 报名审核（社团管理员 / 系统管理员）
# ============================================================
@bp.route('/admin/registrations')
@club_admin_or_sys_required
def registration_review():
    """报名审核：先选活动，再审核该活动的报名列表"""
    activities = _manageable_activities()
    activity_id = request.args.get('activity_id', type=int)
    activity = db.session.get(Activity, activity_id) if activity_id else None
    if activity and not ActivityService.can_manage(activity, current_user):
        abort(403)

    registrations = []
    if activity:
        registrations = RegistrationService.get_activity_registrations(
            activity,
            status=request.args.get('status', '').strip() or None,
            keyword=request.args.get('keyword', '').strip() or None,
        )
    return render_template('admin/registration_review.html',
                           activities=activities, activity=activity,
                           registrations=registrations)


@bp.route('/admin/registration/<int:reg_id>/review', methods=['POST'])
@club_admin_or_sys_required
def registration_review_action(reg_id):
    """审核报名：通过 / 拒绝"""
    registration = db.session.get(Registration, reg_id)
    if not registration:
        abort(404)
    if not ActivityService.can_manage(registration.activity, current_user):
        abort(403)

    action = request.form.get('action', '')
    comment = request.form.get('review_comment', '')
    try:
        RegistrationService.review(registration, action, current_user, comment)
    except RegistrationError as e:
        flash(e.message, 'danger')
    else:
        flash(f'报名审核完成：{registration.status_label}。', 'success')
    return redirect(request.referrer or url_for('admin.registration_review'))


@bp.route('/admin/registration/<int:reg_id>/export', methods=['GET'])
@club_admin_or_sys_required
def registration_export(reg_id):
    """报名名单导出（CSV）"""
    registration = db.session.get(Registration, reg_id)
    if not registration:
        abort(404)
    activity = registration.activity
    if not ActivityService.can_manage(activity, current_user):
        abort(403)
    return _export_registrations_csv(activity)


# ============================================================
# 签到管理（社团管理员 / 系统管理员）
# ============================================================
@bp.route('/admin/checkin')
@club_admin_or_sys_required
def checkin_manage():
    """签到管理：选择活动后展示二维码与签到名单"""
    activities = _manageable_activities()
    activity_id = request.args.get('activity_id', type=int)
    activity = db.session.get(Activity, activity_id) if activity_id else None
    if activity and not ActivityService.can_manage(activity, current_user):
        abort(403)

    context = {'activities': activities, 'activity': activity}
    if activity:
        context['stats'] = CheckinService.activity_stats(activity)
        context['checkins'] = CheckinService.get_activity_checkins(activity)
        context['qr_data_uri'] = None
        if activity.checkin_code and activity.checkin_expire and \
                datetime.now() <= activity.checkin_expire:
            context['qr_data_uri'] = CheckinService.qr_data_uri(
                activity, activity.checkin_code)
    return render_template('admin/checkin_manage.html', **context)


@bp.route('/admin/checkin/generate/<int:activity_id>', methods=['GET', 'POST'])
@club_admin_or_sys_required
def checkin_generate(activity_id):
    """生成签到码（并展示二维码）"""
    activity = _get_manageable_activity(activity_id)
    code = CheckinService.generate_code(activity)
    qr = CheckinService.qr_data_uri(activity, code)
    flash('签到码已生成，二维码有效期为 10 分钟。', 'success')
    return render_template('admin/checkin_qr.html', activity=activity,
                           code=code, qr_data_uri=qr)


@bp.route('/admin/checkin/manual', methods=['POST'])
@club_admin_or_sys_required
def checkin_manual():
    """手动签到（补签）"""
    activity = _get_manageable_activity(request.form.get('activity_id', type=int))
    reg_id = request.form.get('registration_id', type=int)
    registration = db.session.get(Registration, reg_id)
    if not registration or registration.activity_id != activity.id:
        abort(404)
    try:
        CheckinService.manual_checkin(activity, registration)
    except CheckinError as e:
        flash(e.message, 'danger')
    else:
        flash(f'已为 {registration.user.real_name or registration.user.username} 手动签到。', 'success')
    return redirect(url_for('admin.checkin_manage', activity_id=activity.id))


@bp.route('/admin/checkin/export/<int:activity_id>', methods=['GET'])
@club_admin_or_sys_required
def checkin_export(activity_id):
    """签到数据导出（CSV）"""
    activity = _get_manageable_activity(activity_id)
    return _export_checkins_csv(activity)


def _export_registrations_csv(activity):
    """报名名单 CSV"""
    registrations = RegistrationService.get_activity_registrations(activity)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['姓名', '学号', '用户名', '报名时间', '状态', '审核备注'])
    for r in registrations:
        writer.writerow([r.user.real_name or '', r.user.student_id or '',
                         r.user.username,
                         r.apply_time.strftime('%Y-%m-%d %H:%M') if r.apply_time else '',
                         r.status_label, r.review_comment or ''])
    return _csv_response(buf, f'报名名单_{activity.title}.csv')


def _export_checkins_csv(activity):
    """签到数据 CSV"""
    checkins = CheckinService.get_activity_checkins(activity)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['姓名', '学号', '用户名', '签到时间', '签到方式', '状态'])
    for c in checkins:
        writer.writerow([c.user.real_name or '', c.user.student_id or '',
                         c.user.username,
                         c.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if c.checkin_time else '',
                         c.checkin_type_label, c.status_label])
    return _csv_response(buf, f'签到数据_{activity.title}.csv')


def _csv_response(buf, filename):
    data = buf.getvalue().encode('utf-8-sig')  # 带 BOM，Excel 打开不乱码
    from io import BytesIO
    return send_file(BytesIO(data), mimetype='text/csv',
                     as_attachment=True, download_name=filename)


# ============================================================
# 总结归档（社团管理员 / 系统管理员）
# ============================================================
@bp.route('/admin/archive/create', methods=['GET', 'POST'])
@club_admin_or_sys_required
def archive_create():
    """上传活动总结（仅限本社团已结束活动）"""
    activities = [a for a in _manageable_activities()
                  if not a.archive or not a.archive.is_archived]
    if request.method == 'POST':
        activity = _get_manageable_activity(
            request.form.get('activity_id', type=int))
        try:
            attachment = save_attachment(request.files.get('attachment'))
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('admin/archive_form.html', activities=activities,
                                   form=request.form)
        try:
            ArchiveService.create(
                activity=activity,
                summary=request.form.get('summary', ''),
                semester=request.form.get('semester', ''),
                attachment_path=attachment or None,
                archiver=current_user,
            )
        except ArchiveError as e:
            flash(e.message, 'danger')
            return render_template('admin/archive_form.html', activities=activities,
                                   form=request.form)
        ArchiveService.mark_archived(activity)
        flash('活动总结已归档。', 'success')
        return redirect(url_for('admin.archive_list'))
    return render_template('admin/archive_form.html', activities=activities,
                           form={})


@bp.route('/admin/archive')
@club_admin_or_sys_required
def archive_list():
    """归档管理（本社团归档列表）"""
    archives = Archive.query.filter_by(is_archived=True).order_by(
        Archive.archive_time.desc()).all()
    if current_user.is_club_admin:
        archives = [a for a in archives if a.activity.club_id == current_user.club_id]
    return render_template('admin/archive_list.html', archives=archives)


# ============================================================
# 用户管理（系统管理员）
# ============================================================
@bp.route('/admin/users')
@sys_admin_required
def user_list():
    """用户管理"""
    keyword = request.args.get('keyword', '').strip()
    role = request.args.get('role', '').strip()
    q = User.query
    if keyword:
        like = f'%{keyword}%'
        q = q.filter(db.or_(User.username.like(like), User.real_name.like(like),
                            User.student_id.like(like)))
    if role:
        q = q.filter(User.role == role)
    users = q.order_by(User.created_at.desc()).all()
    return render_template('admin/user_list.html', users=users,
                           filters={'keyword': keyword, 'role': role})


@bp.route('/admin/user/<int:user_id>/role', methods=['POST'])
@sys_admin_required
def user_role(user_id):
    """权限分配：修改用户角色（学生/社团管理员/系统管理员）"""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    new_role = request.form.get('role', '')
    if new_role not in (ROLE_STUDENT, ROLE_CLUB_ADMIN, ROLE_SYS_ADMIN):
        flash('非法的角色。', 'danger')
        return redirect(url_for('admin.user_list'))

    # 保护：不能撤销自己的系统管理员身份
    if user.id == current_user.id and new_role != ROLE_SYS_ADMIN:
        flash('不能撤销自己的系统管理员身份。', 'danger')
        return redirect(url_for('admin.user_list'))

    user.role = new_role
    if new_role != ROLE_CLUB_ADMIN and not user.is_sys_admin:
        # 若被降级为非社团管理员，仍可保留社团归属，但仅普通成员
        pass
    db.session.commit()
    flash(f'已更新用户 {user.username} 的角色为「{user.role_label}」。', 'success')
    return redirect(request.referrer or url_for('admin.user_list'))


# ============================================================
# 社团管理（系统管理员）
# ============================================================
@bp.route('/admin/clubs')
@sys_admin_required
def club_list():
    """社团管理"""
    clubs = ClubService.get_all(
        keyword=request.args.get('keyword', '').strip() or None,
        category=request.args.get('category', '').strip() or None)
    return render_template('admin/club_list.html', clubs=clubs,
                           categories=ClubService.all_categories())


@bp.route('/admin/club/create', methods=['GET', 'POST'])
@sys_admin_required
def club_create():
    """创建社团"""
    if request.method == 'POST':
        try:
            club = ClubService.create(
                name=request.form.get('name', ''),
                description=request.form.get('description', ''),
                category=request.form.get('category', ''),
                founder_id=current_user.id,
            )
        except ClubError as e:
            flash(e.message, 'danger')
            return render_template('admin/club_form.html', club=None,
                                   form=request.form)
        flash(f'社团「{club.name}」创建成功。', 'success')
        return redirect(url_for('admin.club_detail', club_id=club.id))
    return render_template('admin/club_form.html', club=None, form={})


@bp.route('/admin/club/<int:club_id>')
@sys_admin_required
def club_detail(club_id):
    """社团详情：成员管理、管理员任命、活动统计"""
    club = db.session.get(Club, club_id)
    if not club:
        abort(404)
    members = club.members.order_by(User.role, User.id).all()
    stats = ClubService.club_stats(club)
    recent_activities = (Activity.query.filter_by(club_id=club.id)
                         .order_by(Activity.created_at.desc()).limit(8).all())
    return render_template('admin/club_detail.html', club=club,
                           members=members, stats=stats,
                           recent_activities=recent_activities)


@bp.route('/admin/club/<int:club_id>/edit', methods=['GET', 'POST'])
@sys_admin_required
def club_edit(club_id):
    """编辑社团"""
    club = db.session.get(Club, club_id)
    if not club:
        abort(404)
    if request.method == 'POST':
        try:
            ClubService.update(
                club=club,
                name=request.form.get('name', ''),
                description=request.form.get('description', ''),
                category=request.form.get('category', ''),
                status=request.form.get('status', ''),
            )
        except ClubError as e:
            flash(e.message, 'danger')
            return render_template('admin/club_form.html', club=club,
                                   form=request.form)
        flash('社团信息已更新。', 'success')
        return redirect(url_for('admin.club_detail', club_id=club.id))
    return render_template('admin/club_form.html', club=club, form={})


@bp.route('/admin/club/<int:club_id>/member', methods=['POST'])
@sys_admin_required
def club_add_member(club_id):
    """添加成员（按用户名）"""
    club = db.session.get(Club, club_id)
    if not club:
        abort(404)
    try:
        ClubService.add_member(club, request.form.get('username', ''))
    except ClubError as e:
        flash(e.message, 'danger')
    else:
        flash('成员添加成功。', 'success')
    return redirect(url_for('admin.club_detail', club_id=club.id))


@bp.route('/admin/club/<int:club_id>/member/<int:user_id>/remove', methods=['POST'])
@sys_admin_required
def club_remove_member(club_id, user_id):
    """移除成员"""
    club = db.session.get(Club, club_id)
    user = db.session.get(User, user_id)
    if not club or not user:
        abort(404)
    try:
        ClubService.remove_member(club, user)
    except ClubError as e:
        flash(e.message, 'danger')
    else:
        flash(f'已将 {user.username} 移出社团。', 'info')
    return redirect(url_for('admin.club_detail', club_id=club.id))


@bp.route('/admin/club/<int:club_id>/member/<int:user_id>/appoint', methods=['POST'])
@sys_admin_required
def club_appoint_admin(club_id, user_id):
    """任命社团管理员"""
    club = db.session.get(Club, club_id)
    user = db.session.get(User, user_id)
    if not club or not user:
        abort(404)
    try:
        ClubService.appoint_admin(club, user)
    except ClubError as e:
        flash(e.message, 'danger')
    else:
        flash(f'已任命 {user.username} 为社团管理员。', 'success')
    return redirect(url_for('admin.club_detail', club_id=club.id))


@bp.route('/admin/club/<int:club_id>/member/<int:user_id>/revoke', methods=['POST'])
@sys_admin_required
def club_revoke_admin(club_id, user_id):
    """解除社团管理员身份"""
    club = db.session.get(Club, club_id)
    user = db.session.get(User, user_id)
    if not club or not user:
        abort(404)
    try:
        ClubService.revoke_admin(club, user)
    except ClubError as e:
        flash(e.message, 'danger')
    else:
        flash(f'已解除 {user.username} 的社团管理员身份。', 'info')
    return redirect(url_for('admin.club_detail', club_id=club.id))
