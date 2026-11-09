# coding=utf-8
"""
    @project: MaxKB
    @file: log_management.py
    @desc: 操作日志（审计日志）接口
"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.exception.app_exception import AppApiException
from common.result import result
from system_manage.serializers.log_management import OperateLogSerializer, get_clean_time, save_clean_time


class OperateLogView(APIView):
    authentication_classes = [TokenAuth]

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['GET'],
            summary=_('Get operation log paginated list'),
            description=_('Get operation log paginated list'),
            operation_id=_('Get operation log paginated list'),  # type: ignore
            tags=[_('Operation Log')],  # type: ignore
        )
        @has_permissions(PermissionConstants.OPERATION_LOG_READ, RoleConstants.ADMIN)
        def get(self, request: Request, current_page: int, page_size: int):
            return result.success(OperateLogSerializer(data=request.query_params).page(current_page, page_size))

    class Menu(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['GET'],
            summary=_('Get operation log menu options'),
            description=_('Get operation log menu options'),
            operation_id=_('Get operation log menu options'),  # type: ignore
            tags=[_('Operation Log')],  # type: ignore
        )
        @has_permissions(PermissionConstants.OPERATION_LOG_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            return result.success(OperateLogSerializer.menu_options())

    class Export(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['POST'],
            summary=_('Export operation log'),
            description=_('Export operation log'),
            operation_id=_('Export operation log'),  # type: ignore
            tags=[_('Operation Log')],  # type: ignore
        )
        @has_permissions(PermissionConstants.OPERATION_LOG_EXPORT, RoleConstants.ADMIN)
        def post(self, request: Request):
            return OperateLogSerializer(data=request.query_params).export()

    class CleanTime(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['GET'],
            summary=_('Get operation log clear policy'),
            description=_('Get operation log clear policy'),
            operation_id=_('Get operation log clear policy'),  # type: ignore
            tags=[_('Operation Log')],  # type: ignore
        )
        @has_permissions(PermissionConstants.OPERATION_LOG_READ, RoleConstants.ADMIN)
        def get(self, request: Request):
            return result.success(get_clean_time())

        @extend_schema(
            methods=['POST'],
            summary=_('Save operation log clear policy'),
            description=_('Save operation log clear policy'),
            operation_id=_('Save operation log clear policy'),  # type: ignore
            tags=[_('Operation Log')],  # type: ignore
        )
        @has_permissions(PermissionConstants.OPERATION_LOG_CLEAR_POLICY, RoleConstants.ADMIN)
        def post(self, request: Request):
            try:
                clean_time = int(request.data.get('clean_time'))
            except (TypeError, ValueError):
                raise AppApiException(500, _('Invalid clean time'))
            if clean_time < 1 or clean_time > 100000:
                raise AppApiException(500, _('Invalid clean time'))
            save_clean_time(clean_time)
            return result.success(True)
