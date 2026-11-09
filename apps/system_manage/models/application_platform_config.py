# coding=utf-8
"""
    @project: MaxKB
    @file: application_platform_config.py
    @desc: 应用第三方平台接入配置（二开）
"""
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin


class ApplicationPlatformConfig(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False,
                          verbose_name='主键id')
    application_id = models.UUIDField(max_length=128, db_index=True, verbose_name='应用id')
    platform = models.CharField(max_length=32, db_index=True, verbose_name='平台类型')
    meta = models.JSONField(default=dict, verbose_name='平台配置')
    is_active = models.BooleanField(default=False, verbose_name='是否启用')

    class Meta:
        db_table = 'application_platform_config'
        unique_together = ('application_id', 'platform')
