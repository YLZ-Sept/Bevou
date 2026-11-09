# coding=utf-8
"""
    @project: MaxKB
    @file: knowledge_chat_user_auth.py
    @desc: 知识库对话用户/用户组授权接口（二开）
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.result import result
from system_manage.serializers.knowledge_chat_user_auth import KnowledgeChatUserAuthSerializer


class KnowledgeChatUserAuthView(APIView):
    authentication_classes = [TokenAuth]

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get knowledge chat user authorization'),
                       operation_id=_('Get knowledge chat user authorization'),
                       tags=[_('Knowledge')])  # type: ignore
        @has_permissions(PermissionConstants.KNOWLEDGE_CHAT_USER_READ, RoleConstants.ADMIN)
        def get(self, request: Request, knowledge_id: str):
            return result.success(KnowledgeChatUserAuthSerializer().info(knowledge_id))

        @extend_schema(methods=['PUT'], summary=_('Update knowledge chat user authorization'),
                       operation_id=_('Update knowledge chat user authorization'),
                       tags=[_('Knowledge')])  # type: ignore
        @has_permissions(PermissionConstants.KNOWLEDGE_CHAT_USER_EDIT, RoleConstants.ADMIN)
        def put(self, request: Request, knowledge_id: str):
            return result.success(KnowledgeChatUserAuthSerializer(data=request.data).update(knowledge_id))
