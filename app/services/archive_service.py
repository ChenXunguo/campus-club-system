# -*- coding: utf-8 -*-
"""总结归档业务逻辑"""
from datetime import datetime

from app import db
from app.models.archive import Archive
from app.models.activity import Activity


class ArchiveError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ArchiveService:
    """活动总结归档 / 检索 / 查看"""

    @staticmethod
    def create(activity: Activity, summary: str, semester: str,
               attachment_path=None, archiver=None) -> Archive:
        """创建活动归档（一个活动仅一份，一对一）"""
        if not summary or not (summary or '').strip():
            raise ArchiveError('活动总结内容不能为空。')

        # 已存在归档则更新
        archive = Archive.query.filter_by(activity_id=activity.id).first()
        if not archive:
            archive = Archive(activity_id=activity.id)
            db.session.add(archive)

        archive.summary = (summary or '').strip()
        archive.semester = (semester or '').strip()
        if attachment_path:
            archive.attachment_path = attachment_path
        archive.archive_time = datetime.now()
        archive.archiver_id = archiver.id if archiver else None
        archive.is_archived = True
        db.session.commit()
        return archive

    @staticmethod
    def mark_archived(activity: Activity) -> None:
        """将活动标记为已归档（用于列表筛选）"""
        activity.status = 'ended'
        db.session.commit()

    @staticmethod
    def get_by_activity(activity_id: int):
        return Archive.query.filter_by(activity_id=activity_id).first()

    @staticmethod
    def search(semester=None, club_id=None, keyword=None):
        """归档检索：按学期 / 社团 / 关键词"""
        q = Archive.query.filter_by(is_archived=True)
        if semester:
            q = q.filter(Archive.semester == semester)
        if club_id:
            q = q.join(Activity).filter(Activity.club_id == club_id)
        if keyword:
            like = f'%{keyword}%'
            q = q.join(Activity).filter(
                db.or_(Activity.title.like(like), Archive.summary.like(like)))
        return q.order_by(Archive.archive_time.desc()).all()

    @staticmethod
    def all_semesters():
        """去重后的学期列表（用于筛选下拉框）"""
        rows = db.session.query(Archive.semester).filter(
            Archive.semester.isnot(None), Archive.semester != '').distinct().all()
        return sorted({r[0] for r in rows}, reverse=True)
