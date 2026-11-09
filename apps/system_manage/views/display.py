# coding=utf-8
"""
    @project: MaxKB
    @file: display.py
    @desc: 外观设置接口
"""
import mimetypes

from django.http import FileResponse, Http404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.result import result
from system_manage.serializers.display import get_display_image_path, get_display_info, save_display_info


class DisplayView(APIView):
    class Info(APIView):
        """外观配置属于登录页展示内容，允许匿名读取（沿用全局 AnonymousAuthentication）"""

        @extend_schema(
            methods=['GET'],
            summary=_('Get display settings'),
            description=_('Get display settings'),
            operation_id=_('Get display settings'),  # type: ignore
            tags=[_('Appearance Settings')],  # type: ignore
        )
        def get(self, request: Request):
            return result.success(get_display_info())

    class Update(APIView):
        authentication_classes = [TokenAuth]
        parser_classes = [MultiPartParser, FormParser, JSONParser]

        @extend_schema(
            methods=['PUT'],
            summary=_('Update display settings'),
            description=_('Update display settings'),
            operation_id=_('Update display settings'),  # type: ignore
            tags=[_('Appearance Settings')],  # type: ignore
        )
        @has_permissions(PermissionConstants.APPEARANCE_SETTINGS_EDIT, RoleConstants.ADMIN)
        def put(self, request: Request):
            return result.success(save_display_info(request.data, request.FILES))


class DisplayImageView(APIView):
    """外观图片为登录页公共资源，无需鉴权"""

    def get(self, request: Request, image_name: str):
        path = get_display_image_path(image_name)
        if path is None:
            raise Http404
        content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        response = FileResponse(open(path, 'rb'), content_type=content_type)
        response['Cache-Control'] = 'public, max-age=3600'
        return response
