# coding=utf-8
"""
    @project: MaxKB
    @file: chat_user_auth.py
    @desc: 对话用户登录 / 资料 / 登出接口（二开）
"""
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from chat.serializers.chat_user_auth import ChatUserLoginSerializer
from common.auth import ChatTokenAuth
from common.exception.app_exception import AppAuthenticationFailed
from common.result import result
from system_manage.models import ChatUser


class ChatUserLoginView(APIView):
    @extend_schema(methods=['POST'], summary=_('Chat user login'),
                   operation_id=_('Chat user login'), tags=[_('Chat')])  # type: ignore
    def post(self, request: Request, access_token: str):
        return result.success(ChatUserLoginSerializer().login(access_token, request.data))


class ChatUserProfileView(APIView):
    authentication_classes = [ChatTokenAuth]

    @extend_schema(methods=['GET'], summary=_('Get chat user profile'),
                   operation_id=_('Get chat user profile'), tags=[_('Chat')])  # type: ignore
    def get(self, request: Request):
        chat_user = QuerySet(ChatUser).filter(id=request.auth.chat_user_id, is_active=True).first()
        if chat_user is None:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        return result.success({
            'id': str(chat_user.id),
            'username': chat_user.username,
            'nick_name': chat_user.nick_name,
            'email': chat_user.email or '',
            'phone': chat_user.phone or '',
        })


class ChatUserLogoutView(APIView):
    authentication_classes = [ChatTokenAuth]

    @extend_schema(methods=['POST'], summary=_('Chat user logout'),
                   operation_id=_('Chat user logout'), tags=[_('Chat')])  # type: ignore
    def post(self, request: Request):
        return result.success(True)
