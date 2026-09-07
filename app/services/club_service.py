# -*- coding: utf-8 -*-
"""社团与成员管理业务逻辑"""
from app import db
from app.models.club import Club
from app.models.user import User, ROLE_CLUB_ADMIN, ROLE_STUDENT


class ClubError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ClubService:
    """社团创建、编辑、成员管理、管理员任命、统计"""

    # ---- 社团信息 ----
    @staticmethod
    def create(name, description, category, founder_id=None) -> Club:
        name = (name or '').strip()
        if not name:
            raise ClubError('社团名称不能为空。')
        if Club.query.filter_by(name=name).first():
            raise ClubError('该社团已存在。')
        club = Club(name=name, description=description or '',
                    category=(category or '').strip(), founder_id=founder_id)
        db.session.add(club)
        db.session.commit()
        return club

    @staticmethod
    def update(club: Club, name, description, category, status=None) -> None:
        name = (name or '').strip()
        if not name:
            raise ClubError('社团名称不能为空。')
        dup = Club.query.filter(Club.name == name, Club.id != club.id).first()
        if dup:
            raise ClubError('该社团名称已被占用。')
        club.name = name
        club.description = description or ''
        club.category = (category or '').strip()
        if status in ('active', 'inactive'):
            club.status = status
        db.session.commit()

    @staticmethod
    def get_all(keyword=None, category=None):
        q = Club.query
        if keyword:
            like = f'%{keyword}%'
            q = q.filter(db.or_(Club.name.like(like), Club.description.like(like)))
        if category:
            q = q.filter(Club.category == category)
        return q.order_by(Club.created_at.desc()).all()

    @staticmethod
    def all_categories():
        rows = db.session.query(Club.category).filter(
            Club.category.isnot(None), Club.category != '').distinct().all()
        return sorted({r[0] for r in rows})

    # ---- 成员管理 ----
    @staticmethod
    def add_member(club: Club, username) -> User:
        """将用户加入社团（按用户名检索）"""
        username = (username or '').strip()
        user = User.query.filter_by(username=username).first()
        if not user:
            raise ClubError('未找到该用户名对应的用户。')
        if user.club_id:
            if user.club_id == club.id:
                raise ClubError('该用户已是本社团成员。')
            raise ClubError(f'该用户已属于其他社团（{user.club.name}）。')
        user.club_id = club.id
        if user.is_student:
            user.role = ROLE_STUDENT  # 加入社团的学生角色不变
        db.session.commit()
        return user

    @staticmethod
    def remove_member(club: Club, user: User) -> None:
        """将成员移出社团（系统管理员操作）"""
        if user.club_id != club.id:
            raise ClubError('该用户不属于本社团。')
        if user.is_club_admin and user.club_id == club.id:
            raise ClubError('请先解除其社团管理员身份，再移出成员。')
        user.club_id = None
        db.session.commit()

    @staticmethod
    def appoint_admin(club: Club, user: User) -> None:
        """任命社团管理员"""
        if user.club_id != club.id:
            raise ClubError('该用户不是本社团成员，无法任命为管理员。')
        user.role = ROLE_CLUB_ADMIN
        db.session.commit()

    @staticmethod
    def revoke_admin(club: Club, user: User) -> None:
        """解除社团管理员身份（降为学生）"""
        if user.role != ROLE_CLUB_ADMIN or user.club_id != club.id:
            raise ClubError('该用户不是本社团管理员。')
        user.role = ROLE_STUDENT
        db.session.commit()

    # ---- 统计 ----
    @staticmethod
    def club_stats(club: Club):
        """社团活动统计：总活动数、进行中、已结束、报名人次、签到人次"""
        from app.models.activity import Activity
        from app.models.registration import Registration, REG_APPROVED
        from app.models.checkin import Checkin

        activities = club.activities.all()
        total = len(activities)
        ongoing = sum(1 for a in activities if a.status == 'ongoing')
        ended = sum(1 for a in activities if a.status == 'ended')
        registration_count = Registration.query.join(Activity).filter(
            Activity.club_id == club.id, Registration.status == REG_APPROVED).count()
        checkin_count = Checkin.query.join(Activity).filter(
            Activity.club_id == club.id).count()
        return {
            'total': total,
            'ongoing': ongoing,
            'ended': ended,
            'registrations': registration_count,
            'checkins': checkin_count,
        }
