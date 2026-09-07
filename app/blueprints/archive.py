# -*- coding: utf-8 -*-
"""归档模块蓝图：归档列表检索、归档详情查看"""
from flask import (Blueprint, abort, render_template, request)

from app import db
from app.models.archive import Archive
from app.models.club import Club
from app.services.activity_service import ActivityService
from app.services.archive_service import ArchiveService

bp = Blueprint('archive', __name__)


@bp.route('/archives')
def list_archives():
    """归档列表：按学期 / 社团 / 关键词检索"""
    semester = request.args.get('semester', '').strip()
    club_id = request.args.get('club_id', '').strip()
    keyword = request.args.get('keyword', '').strip()

    archives = ArchiveService.search(
        semester=semester or None,
        club_id=int(club_id) if club_id.isdigit() else None,
        keyword=keyword or None,
    )
    return render_template('archive/list.html',
                           archives=archives,
                           semesters=ArchiveService.all_semesters(),
                           clubs=ActivityService.get_clubs(),
                           filters={'semester': semester, 'club_id': club_id,
                                    'keyword': keyword})


@bp.route('/archive/<int:archive_id>')
def detail(archive_id):
    """归档详情查看"""
    archive = db.session.get(Archive, archive_id)
    if not archive or not archive.is_archived:
        abort(404)
    return render_template('archive/detail.html', archive=archive)


@bp.route('/archive/activity/<int:activity_id>')
def by_activity(activity_id):
    """按活动查看归档"""
    archive = ArchiveService.get_by_activity(activity_id)
    if not archive or not archive.is_archived:
        abort(404)
    return render_template('archive/detail.html', archive=archive)
