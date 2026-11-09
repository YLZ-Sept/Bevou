# coding=utf-8
"""
    @project: MaxKB
    @file: platform_config.py
    @desc: 应用第三方平台接入配置接口（二开）
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from application.serializers.platform_config import PlatformConfigSerializer
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import (
    CompareConstants, PermissionConstants, RoleConstants, ViewPermission,
)
from common.result import result


def platform_permissions():
    return [
        PermissionConstants.APPLICATION_OVERVIEW_ACCESS.get_workspace_application_permission(),
        PermissionConstants.APPLICATION_OVERVIEW_ACCESS.get_workspace_permission_workspace_manage_role(),
        ViewPermission([RoleConstants.USER.get_workspace_role()],
                       [PermissionConstants.APPLICATION.get_workspace_application_permission()],
                       CompareConstants.AND),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        RoleConstants.ADMIN,
    ]


class ApplicationPlatformView(APIView):
    authentication_classes = [TokenAuth]

    class Status(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get platform access status'),
                       operation_id=_('Get platform access status'), tags=[_('Application')])  # type: ignore
        @has_permissions(*platform_permissions())
        def get(self, request: Request, workspace_id: str, application_id: str):
            return result.success(PlatformConfigSerializer.status(application_id))

        @extend_schema(methods=['POST'], summary=_('Update platform access status'),
                       operation_id=_('Update platform access status'), tags=[_('Application')])  # type: ignore
        @has_permissions(*platform_permissions())
        def post(self, request: Request, workspace_id: str, application_id: str):
            return result.success(PlatformConfigSerializer.update_status(application_id, request.data))

    class Config(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(methods=['GET'], summary=_('Get platform config'),
                       operation_id=_('Get platform config'), tags=[_('Application')])  # type: ignore
        @has_permissions(*platform_permissions())
        def get(self, request: Request, workspace_id: str, application_id: str, platform: str):
            return result.success(PlatformConfigSerializer.get(application_id, platform))

        @extend_schema(methods=['POST'], summary=_('Update platform config'),
                       operation_id=_('Update platform config'), tags=[_('Application')])  # type: ignore
        @has_permissions(*platform_permissions())
        def post(self, request: Request, workspace_id: str, application_id: str, platform: str):
            return result.success(PlatformConfigSerializer.save(application_id, platform, request.data))
