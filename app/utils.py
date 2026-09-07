# -*- coding: utf-8 -*-
"""通用工具：文件上传等"""
import os
import uuid
from datetime import datetime

from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
ALLOWED_ATTACHMENT_EXT = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                          'txt', 'zip', 'rar', 'md'}


def _ext(filename: str) -> str:
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def save_upload(file_storage, subdir: str, allowed_ext, max_size=None) -> str:
    """保存上传文件，返回相对路径（相对 static/uploads/ 的子路径）。
    返回的路径格式：covers/xxxx.ext 或 attachments/xxxx.ext
    """
    if not file_storage or not file_storage.filename:
        return ''
    ext = _ext(file_storage.filename)
    if ext not in allowed_ext:
        raise ValueError(f'不支持的文件类型：.{ext or "未知"}')

    if max_size:
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
        if size > max_size:
            raise ValueError('文件大小超出限制。')

    # 使用随机文件名避免中文/冲突
    new_name = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{uuid.uuid4().hex[:8]}.{ext}'
    rel_dir = os.path.join(subdir)
    abs_dir = os.path.join(_upload_base(), subdir)
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, new_name)
    file_storage.save(abs_path)
    return os.path.join(rel_dir, new_name).replace('\\', '/')


def _upload_base():
    from flask import current_app
    return current_app.config['UPLOAD_FOLDER']


def save_cover(file_storage) -> str:
    """保存活动封面图"""
    return save_upload(file_storage, 'covers', ALLOWED_IMAGE_EXT)


def save_attachment(file_storage) -> str:
    """保存归档附件"""
    return save_upload(file_storage, 'attachments', ALLOWED_ATTACHMENT_EXT)
