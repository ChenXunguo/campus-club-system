# -*- coding: utf-8 -*-
"""
核心功能测试：覆盖项目说明书 8.2 功能测试用例
TC-01 ~ TC-14
"""
from datetime import datetime, timedelta

from app import db
from app.models.activity import Activity
from app.models.archive import Archive
from app.models.checkin import Checkin
from app.models.registration import Registration
from app.models.user import User


def _user_id(username):
    """按用户名获取用户 id（避免依赖自增顺序）"""
    return User.query.filter_by(username=username).first().id


# ---------- 认证 ----------
def test_tc01_login_success(client, login_helpers):
    """TC-01 正确账号密码登录 → 登录成功，跳转首页"""
    resp = login_helpers['login'](client, 'student1', '123456')
    assert resp.status_code == 200
    assert '欢迎回来' in resp.get_data(as_text=True)


def test_tc02_login_wrong_password(client, login_helpers):
    """TC-02 错误密码登录 → 登录失败，提示错误"""
    resp = login_helpers['login'](client, 'student1', 'wrongpass')
    assert '用户名或密码错误' in resp.get_data(as_text=True)


# ---------- 活动 ----------
def _create_activity(club_id, title='测试活动', max_n=10, status='pending'):
    now = datetime.now()
    a = Activity(club_id=club_id, title=title, location='测试楼 101',
                 start_time=now + timedelta(days=1),
                 end_time=now + timedelta(days=1, hours=2),
                 max_participants=max_n, status=status)
    db.session.add(a)
    db.session.commit()
    return a


def test_tc03_club_admin_publish_activity(client, login_helpers):
    """TC-03 社团管理员发布活动 → 活动创建成功"""
    login_helpers['login'](client, 'clubadmin', '123456')
    now = datetime.now()
    resp = client.post('/admin/activity/create', data={
        'club_id': 1, 'title': 'TC03 篮球对抗赛',
        'description': '测试详情', 'location': '东区球场',
        'start_time': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=2, hours=2)).strftime('%Y-%m-%dT%H:%M'),
        'max_participants': 10,
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Activity.query.filter_by(title='TC03 篮球对抗赛').first() is not None


def test_tc04_student_publish_forbidden(client, login_helpers):
    """TC-04 普通学生发布活动 → 权限不足，403"""
    login_helpers['login'](client, 'student1', '123456')
    resp = client.get('/admin/activity/create')
    assert resp.status_code == 403


# ---------- 报名 ----------
def test_tc05_student_apply(client, login_helpers):
    """TC-05 学生报名活动 → 报名记录创建，状态待审核"""
    a = _create_activity(1)
    sid = _user_id('student1')
    login_helpers['login'](client, 'student1', '123456')
    client.post(f'/activity/{a.id}/register', follow_redirects=True)
    reg = Registration.query.filter_by(activity_id=a.id, user_id=sid).first()
    assert reg is not None
    assert reg.status == 'pending'
    assert a.current_participants == 1


def test_tc06_duplicate_apply_rejected(client, login_helpers):
    """TC-06 同一学生重复报名同一活动 → 提示已报名，禁止重复"""
    a = _create_activity(1)
    login_helpers['login'](client, 'student1', '123456')
    client.post(f'/activity/{a.id}/register', follow_redirects=True)
    resp = client.post(f'/activity/{a.id}/register', follow_redirects=True)
    assert '请勿重复报名' in resp.get_data(as_text=True)
    assert Registration.query.filter_by(activity_id=a.id).count() == 1


def test_tc07_full_activity_apply_rejected(client, login_helpers):
    """TC-07 报名人数已达上限 → 提示已满，无法报名"""
    a = _create_activity(1, max_n=1)
    a.current_participants = 1
    db.session.commit()
    login_helpers['login'](client, 'student1', '123456')
    resp = client.post(f'/activity/{a.id}/register', follow_redirects=True)
    assert '报名人数已满' in resp.get_data(as_text=True)


# ---------- 审核 ----------
def _make_pending_registration(activity_id, user_id):
    reg = Registration(activity_id=activity_id, user_id=user_id)
    db.session.add(reg)
    db.session.commit()
    return reg


def test_tc08_review_approve(client, login_helpers):
    """TC-08 管理员审核通过报名 → 状态变为已通过"""
    a = _create_activity(1)
    reg = _make_pending_registration(a.id, _user_id('student1'))
    login_helpers['login'](client, 'clubadmin', '123456')
    client.post(f'/admin/registration/{reg.id}/review',
                data={'action': 'approve'}, follow_redirects=True)
    db.session.refresh(reg)
    assert reg.status == 'approved'
    assert reg.review_time is not None


def test_tc09_review_reject(client, login_helpers):
    """TC-09 管理员审核拒绝报名 → 状态变为已拒绝"""
    a = _create_activity(1)
    reg = _make_pending_registration(a.id, _user_id('student1'))
    login_helpers['login'](client, 'clubadmin', '123456')
    client.post(f'/admin/registration/{reg.id}/review',
                data={'action': 'reject', 'review_comment': '名额已满'},
                follow_redirects=True)
    db.session.refresh(reg)
    assert reg.status == 'rejected'
    assert reg.review_comment == '名额已满'


# ---------- 签到 ----------
def test_tc10_qr_checkin_success(client, login_helpers):
    """TC-10 扫描签到二维码 → 签到成功，记录签到时间"""
    a = _create_activity(1)
    a.status = 'ongoing'
    # 生成签到码
    from app.services.checkin_service import CheckinService
    code = CheckinService.generate_code(a)
    # student1 报名并通过
    sid = _user_id('student1')
    reg = Registration(activity_id=a.id, user_id=sid, status='approved')
    db.session.add(reg)
    db.session.commit()

    login_helpers['login'](client, 'student1', '123456')
    resp = client.get(f'/checkin/{a.id}?code={code}', follow_redirects=True)
    assert '签到成功' in resp.get_data(as_text=True)
    ck = Checkin.query.filter_by(activity_id=a.id, user_id=sid).first()
    assert ck is not None
    assert ck.checkin_time is not None
    assert ck.status == 'success'


def test_tc11_unregistered_checkin_failed(client, login_helpers):
    """TC-11 未报名用户扫码签到 → 签到失败，提示未报名"""
    a = _create_activity(1)
    a.status = 'ongoing'
    from app.services.checkin_service import CheckinService
    code = CheckinService.generate_code(a)
    # student2 未报名
    login_helpers['login'](client, 'student2', '123456')
    resp = client.get(f'/checkin/{a.id}?code={code}', follow_redirects=True)
    assert '未报名' in resp.get_data(as_text=True)


# ---------- 归档 ----------
def test_tc12_upload_archive(client, login_helpers):
    """TC-12 上传活动总结 → 总结保存，活动标记已归档"""
    a = _create_activity(1, status='ended')
    login_helpers['login'](client, 'clubadmin', '123456')
    resp = client.post('/admin/archive/create', data={
        'activity_id': a.id, 'semester': '2026-2027-1',
        'summary': '<p>TC12 活动总结</p>',
    }, follow_redirects=True)
    assert resp.status_code == 200
    ar = Archive.query.filter_by(activity_id=a.id).first()
    assert ar is not None
    assert ar.is_archived is True
    assert ar.semester == '2026-2027-1'


def test_tc13_search_archive_by_semester(client, login_helpers):
    """TC-13 按学期检索归档 → 返回对应学期归档列表"""
    from app.services.archive_service import ArchiveService
    login_helpers['login'](client, 'clubadmin', '123456')
    a = _create_activity(1, status='ended')
    ArchiveService.create(a, '<p>学期检索测试</p>', '2026-2027-1', None,
                          archiver=None)
    results = ArchiveService.search(semester='2026-2027-1')
    assert any(x.activity_id == a.id for x in results)


# ---------- 权限 ----------
def test_tc14_student_access_admin_403(client, login_helpers):
    """TC-14 学生访问管理员页面 → 403 禁止访问"""
    login_helpers['login'](client, 'student1', '123456')
    for url in ['/admin/activities', '/admin/registrations',
                '/admin/checkin', '/admin/users', '/admin/clubs']:
        resp = client.get(url)
        assert resp.status_code == 403, f'{url} 应返回 403'
