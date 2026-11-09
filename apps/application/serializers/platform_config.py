# coding=utf-8
"""
    @project: MaxKB
    @file: platform_config.py
    @desc: 应用第三方平台接入配置（二开）
"""
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from system_manage.models import ApplicationPlatformConfig

PLATFORMS = ['wecomBot', 'wecom', 'dingtalk', 'wechat', 'lark', 'slack']


class PlatformConfigSerializer(serializers.Serializer):
    @staticmethod
    def status(application_id: str) -> dict:
        result = {platform: [False, False] for platform in PLATFORMS}
        rows = QuerySet(ApplicationPlatformConfig).filter(application_id=application_id)
        for row in rows:
            result[row.platform] = [True, row.is_active]
        return result

    @staticmethod
    def update_status(application_id: str, data: dict):
        platform = data.get('type')
        if platform not in PLATFORMS:
            raise AppApiException(500, _('Unsupported platform'))
        row = QuerySet(ApplicationPlatformConfig).filter(
            application_id=application_id, platform=platform
        ).first()
        if row is None:
            row = ApplicationPlatformConfig(application_id=application_id, platform=platform, meta={})
        row.is_active = bool(data.get('status'))
        row.save()
        return True

    @staticmethod
    def get(application_id: str, platform: str) -> dict:
        if platform not in PLATFORMS:
            raise AppApiException(500, _('Unsupported platform'))
        row = QuerySet(ApplicationPlatformConfig).filter(
            application_id=application_id, platform=platform
        ).first()
        return dict(row.meta) if row is not None else {}

    @staticmethod
    def save(application_id: str, platform: str, data: dict):
        if platform not in PLATFORMS:
            raise AppApiException(500, _('Unsupported platform'))
        meta = {key: value for key, value in dict(data).items() if key not in ('callback_url',)}
        row = QuerySet(ApplicationPlatformConfig).filter(
            application_id=application_id, platform=platform
        ).first()
        if row is None:
            row = ApplicationPlatformConfig(application_id=application_id, platform=platform, meta={})
        row.meta = meta
        row.is_active = True
        row.save()
        return True
