# coding=utf-8
"""
    @project: MaxKB
    @file: chat_display.py
    @desc: 对话端读取系统外观配置（二开：让对话页使用统一的 Logo/名称）
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common.result import result
from maxkb.const import CONFIG
from system_manage.serializers.display import get_display_info


class ChatDisplayInfoView(APIView):
    @extend_schema(methods=['GET'], summary=_('Get display settings for chat'),
                   operation_id=_('Get display settings for chat'), tags=[_('Chat')])  # type: ignore
    def get(self, request: Request):
        # 图片地址使用 chat 前缀，保证对话端可直接加载
        return result.success(get_display_info(prefix=CONFIG.get_chat_path()))
