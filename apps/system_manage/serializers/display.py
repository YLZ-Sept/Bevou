# coding=utf-8
"""
    @project: MaxKB
    @file: display.py
    @desc: 外观设置（Logo、名称、标语、主题色、官方入口开关）
"""
import os
import uuid

from django.utils.translation import gettext_lazy as _

from common.exception.app_exception import AppApiException
from maxkb.const import CONFIG, PROJECT_DIR
from system_manage.models.system_setting import SystemSetting, SettingType

DISPLAY_DIR = os.path.join(PROJECT_DIR, 'data', 'display')

IMAGE_FIELDS = ('icon', 'loginLogo', 'loginImage')
TEXT_FIELDS = ('theme', 'title', 'slogan', 'projectUrl', 'userManualUrl', 'forumUrl')
BOOL_FIELDS = ('showProject', 'showUserManual', 'showForum')

# 仅允许安全的位图格式，避免上传 svg 造成同源脚本注入
ALLOWED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

DEFAULT_DISPLAY = {
    'theme': '#3370FF',
    'icon': '',
    'loginLogo': '',
    'loginImage': '',
    'title': 'Bevou｜贝御',
    'slogan': '强大易用的企业级智能体平台',
    'showProject': True,
    'projectUrl': 'https://github.com/1Panel-dev/MaxKB',
    'showUserManual': True,
    'userManualUrl': 'https://docs.fit2cloud.com/maxkb/',
    'showForum': True,
    'forumUrl': 'https://bbs.fit2cloud.com/c/mk/11',
}


def image_url(name: str) -> str:
    if not name:
        return ''
    return f'{CONFIG.get_admin_path()}/api/display/image/{name}'


def get_display_image_path(name: str):
    """返回安全的图片绝对路径，不存在时返回 None"""
    safe_name = os.path.basename(name or '')
    if not safe_name:
        return None
    path = os.path.join(DISPLAY_DIR, safe_name)
    return path if os.path.isfile(path) else None


def _load_meta() -> dict:
    setting = SystemSetting.objects.filter(type=SettingType.DISPLAY).first()
    if setting is not None and isinstance(setting.meta, dict):
        return dict(setting.meta)
    return {}


def _save_setting(meta: dict):
    setting = SystemSetting.objects.filter(type=SettingType.DISPLAY).first()
    if setting is None:
        SystemSetting(type=SettingType.DISPLAY, meta=meta).save()
    else:
        setting.meta = meta
        setting.save()


def _save_image(upload) -> str:
    ext = os.path.splitext(upload.name or '')[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise AppApiException(500, _('Unsupported image format'))
    os.makedirs(DISPLAY_DIR, exist_ok=True)
    name = f'{uuid.uuid4().hex}{ext}'
    with open(os.path.join(DISPLAY_DIR, name), 'wb') as f:
        for chunk in upload.chunks():
            f.write(chunk)
    return name


def _delete_image(name: str):
    if not name:
        return
    try:
        path = os.path.join(DISPLAY_DIR, os.path.basename(name))
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def get_display_info() -> dict:
    meta = _load_meta()
    info = dict(DEFAULT_DISPLAY)
    for key in TEXT_FIELDS:
        if key in meta and meta.get(key) not in (None, ''):
            info[key] = meta.get(key)
    for key in BOOL_FIELDS:
        if key in meta:
            info[key] = bool(meta.get(key))
    for key in IMAGE_FIELDS:
        info[key] = image_url(meta.get(key))
    return info


def save_display_info(data, files) -> bool:
    meta = _load_meta()

    for key in TEXT_FIELDS:
        if key in data:
            meta[key] = data.get(key)

    for key in BOOL_FIELDS:
        if key in data:
            meta[key] = str(data.get(key)).lower() in ('true', '1', 'yes')

    for key in IMAGE_FIELDS:
        upload = files.get(key) if files else None
        if upload is not None:
            new_name = _save_image(upload)
            _delete_image(meta.get(key))
            meta[key] = new_name
        elif key in data:
            value = str(data.get(key) or '').strip()
            # 前端回传当前图片 URL 时保持原样，空字符串表示恢复默认
            if value == '':
                _delete_image(meta.get(key))
                meta.pop(key, None)

    _save_setting(meta)
    return True
