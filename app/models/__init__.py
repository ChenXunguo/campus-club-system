# -*- coding: utf-8 -*-
"""数据模型包"""
from app.models.user import User
from app.models.club import Club
from app.models.activity import Activity
from app.models.registration import Registration
from app.models.checkin import Checkin
from app.models.archive import Archive

__all__ = ['User', 'Club', 'Activity', 'Registration', 'Checkin', 'Archive']
