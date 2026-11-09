# coding=utf-8
"""
    @project: MaxKB
    @file: chat_user.py
    @desc: 对话用户 / 用户组管理接口
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.result import result
from system_manage.serializers.chat_user import ChatUserSerializer, UserGroupSerializer


class ChatUserView(APIView):
    authentication_classes = [TokenAuth]

    class List(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get chat user list'),
                       operation_id=_('Get chat user list'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            return result.success(ChatUserSerializer.list_users())

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get chat user paginated list'),
                       operation_id=_('Get chat user paginated list'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_READ, RoleConstants.ADMIN)
        def get(self, request: Request, current_page: int, page_size: int):
            return result.success(
                ChatUserSerializer(data=request.query_params).page(current_page, page_size, request.query_params)
            )

    class Create(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['POST'], summary=_('Create chat user'),
                       operation_id=_('Create chat user'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_CREATE, RoleConstants.ADMIN)
        def post(self, request: Request):
            return result.success(ChatUserSerializer(data=request.data).save())

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['PUT'], summary=_('Update chat user'),
                       operation_id=_('Update chat user'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_EDIT, RoleConstants.ADMIN)
        def put(self, request: Request, user_id: str):
            return result.success(ChatUserSerializer(data=request.data).edit(user_id))

        @extend_schema(methods=['DELETE'], summary=_('Delete chat user'),
                       operation_id=_('Delete chat user'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_DELETE, RoleConstants.ADMIN)
        def delete(self, request: Request, user_id: str):
            return result.success(ChatUserSerializer.delete(user_id))

    class Password(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['PUT'], summary=_('Update chat user password'),
                       operation_id=_('Update chat user password'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_EDIT, RoleConstants.ADMIN)
        def put(self, request: Request, user_id: str):
            return result.success(ChatUserSerializer(data=request.data).re_password(user_id))

    class BatchAddGroup(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['POST'], summary=_('Batch set chat user groups'),
                       operation_id=_('Batch set chat user groups'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_GROUP, RoleConstants.ADMIN)
        def post(self, request: Request):
            return result.success(ChatUserSerializer(data=request.data).batch_add_group())

    class BatchDelete(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['POST'], summary=_('Batch delete chat users'),
                       operation_id=_('Batch delete chat users'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_DELETE, RoleConstants.ADMIN)
        def post(self, request: Request):
            return result.success(ChatUserSerializer.batch_delete(request.data))

    class SyncTypes(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get chat user sync types'),
                       operation_id=_('Get chat user sync types'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            return result.success(ChatUserSerializer.sync_types())

    class Sync(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['POST'], summary=_('Sync chat users'),
                       operation_id=_('Sync chat users'), tags=[_('Chat User')])  # type: ignore
        @has_permissions(PermissionConstants.CHAT_USER_SYNC, RoleConstants.ADMIN)
        def post(self, request: Request, sync_type: str):
            return result.success(ChatUserSerializer.sync(sync_type))


class UserGroupView(APIView):
    authentication_classes = [TokenAuth]

    class List(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get user group list'),
                       operation_id=_('Get user group list'), tags=[_('User Group')])  # type: ignore
        @has_permissions(PermissionConstants.USER_GROUP_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            return result.success(UserGroupSerializer.list_groups())

        @extend_schema(methods=['POST'], summary=_('Create or rename user group'),
                       operation_id=_('Create or rename user group'), tags=[_('User Group')])  # type: ignore
        @has_permissions(PermissionConstants.USER_GROUP_CREATE, PermissionConstants.USER_GROUP_EDIT,
                         RoleConstants.ADMIN)
        def post(self, request: Request):
            return result.success(UserGroupSerializer(data=request.data).save())

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['DELETE'], summary=_('Delete user group'),
                       operation_id=_('Delete user group'), tags=[_('User Group')])  # type: ignore
        @has_permissions(PermissionConstants.USER_GROUP_DELETE, RoleConstants.ADMIN)
        def delete(self, request: Request, group_id: str):
            return result.success(UserGroupSerializer.delete(group_id))

    class AddMember(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['POST'], summary=_('Add user group members'),
                       operation_id=_('Add user group members'), tags=[_('User Group')])  # type: ignore
        @has_permissions(PermissionConstants.USER_GROUP_ADD_MEMBER, RoleConstants.ADMIN)
        def post(self, request: Request, group_id: str):
            return result.success(UserGroupSerializer(data=request.data).add_member(group_id))

    class RemoveMember(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['POST'], summary=_('Remove user group members'),
                       operation_id=_('Remove user group members'), tags=[_('User Group')])  # type: ignore
        @has_permissions(PermissionConstants.USER_GROUP_REMOVE_MEMBER, RoleConstants.ADMIN)
        def post(self, request: Request, group_id: str):
            return result.success(UserGroupSerializer(data=request.data).remove_member(group_id))

    class UserPage(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get user group members'),
                       operation_id=_('Get user group members'), tags=[_('User Group')])  # type: ignore
        @has_permissions(PermissionConstants.USER_GROUP_READ, RoleConstants.ADMIN)
        def get(self, request: Request, group_id: str, current_page: int, page_size: int):
            return result.success(
                UserGroupSerializer.page_users(group_id, current_page, page_size, request.query_params)
            )
