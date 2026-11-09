# coding=utf-8
"""
    @project: MaxKB
    @file: chat_user_token.py
    @desc: 已登录对话用户 token 鉴权（二开：LOCAL 登录）
"""
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from application.models import ApplicationAccessToken, ChatUserType
from common.auth.common import ChatUserToken
from common.auth.handle.auth_base_handle import AuthBaseHandle
from common.constants.authentication_type import AuthenticationType
from common.constants.permission_constants import RoleConstants, Permission, Group, Operate, ChatAuth
from common.exception.app_exception import AppAuthenticationFailed
from system_manage.models import ChatUser


class ChatUserTokenAuth(AuthBaseHandle):
    def support(self, request, token: str, get_token_details):
        token_details = get_token_details()
        if token_details is None:
            return False
        return (
                'application_id' in token_details and
                'access_token' in token_details and
                'chat_user_id' in token_details and
                token_details.get('type') == AuthenticationType.CHAT_USER.value
        )

    def handle(self, request, token: str, get_token_details):
        auth_details = get_token_details()
        chat_user_token = ChatUserToken.new_instance(auth_details)
        application_access_token = QuerySet(ApplicationAccessToken).filter(
            application_id=chat_user_token.application_id).first()
        if application_access_token is None or not application_access_token.is_active:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        if application_access_token.access_token != chat_user_token.access_token:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        chat_user = QuerySet(ChatUser).filter(id=chat_user_token.chat_user_id, is_active=True).first()
        if chat_user is None:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        return None, ChatAuth(
            current_role_list=[RoleConstants.CHAT_USER],
            permission_list=[Permission(group=Group.APPLICATION, operate=Operate.USE)],
            application_id=application_access_token.application_id,
            chat_user_id=str(chat_user.id),
            chat_user_type=ChatUserType.CHAT_USER)
