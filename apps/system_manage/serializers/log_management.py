# coding=utf-8
"""
    @project: MaxKB
    @file: log_management.py
    @desc: 操作日志（审计日志）查询、导出与清理策略
"""
import json
from datetime import datetime, timedelta
from io import BytesIO

import openpyxl
from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _, get_language
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from rest_framework import serializers

from common.db.search import page_search
from system_manage.models import Log
from system_manage.models.system_setting import SystemSetting, SettingType

DEFAULT_CLEAN_TIME = 180

# 个别菜单名的翻译在语言包里缺失或含义不符，这里做覆盖
MENU_LABEL_OVERRIDES = {
    'tag': '标签',
    'termbase': '术语库',
    'problem': '问题',
}

# 历史数据里同一个菜单存在多种写法，查询与展示时统一归并
MENU_CANONICAL = {
    'Knowledge Base': 'Knowledge',
    'knowledge Base': 'Knowledge',
}

EXPORT_HEADERS = {
    'zh': ['菜单', '操作详情', '用户', '状态', 'IP 地址', '操作时间'],
    'en': ['Menu', 'Operation details', 'User', 'Status', 'IP Address', 'Operation time'],
}


def canonical_menu(menu: str) -> str:
    return MENU_CANONICAL.get(menu, menu)


def is_zh_language() -> bool:
    return str(get_language() or '').lower().startswith('zh')

# 预估菜单全集，用于在还没有日志时也能给出筛选项
KNOWN_MENUS = [
    'Application',
    'Knowledge',
    'Knowledge Base',
    'knowledge Base',
    'document',
    'Paragraph',
    'problem',
    'tag',
    'termbase',
    'Tool',
    'model',
    'file',
    'folder',
    'Trigger',
    'User management',
    'Email settings',
    'System',
]


def get_menu_label(menu: str) -> str:
    if menu in MENU_LABEL_OVERRIDES:
        return MENU_LABEL_OVERRIDES.get(menu)
    return str(_(menu))


def _parse_date(value, end_of_day=False):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        dt = None
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(text, fmt)
                if fmt == '%Y-%m-%d' and end_of_day:
                    dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                break
            except ValueError:
                continue
        if dt is None:
            return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _parse_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _cell_value(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return ILLEGAL_CHARACTERS_RE.sub('', str(value))


def get_clean_time() -> int:
    setting = SystemSetting.objects.filter(type=SettingType.LOG).first()
    if setting is not None and isinstance(setting.meta, dict):
        try:
            return int(setting.meta.get('clean_time', DEFAULT_CLEAN_TIME))
        except (TypeError, ValueError):
            return DEFAULT_CLEAN_TIME
    return DEFAULT_CLEAN_TIME


def clean_expired_log(clean_time: int = None):
    days = get_clean_time() if clean_time is None else int(clean_time)
    # 避免异常配置导致日志被全部清空
    if days < 1:
        return
    cutoff = timezone.now() - timedelta(days=days)
    QuerySet(Log).filter(create_time__lt=cutoff).delete()


def save_clean_time(clean_time: int):
    setting = SystemSetting.objects.filter(type=SettingType.LOG).first()
    if setting is None:
        SystemSetting(type=SettingType.LOG, meta={'clean_time': clean_time}).save()
    else:
        setting.meta = {**(setting.meta or {}), 'clean_time': clean_time}
        setting.save()
    clean_expired_log(clean_time)


class OperateLogSerializer(serializers.Serializer):
    start_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    end_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    user = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ip_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    menu = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    workspace_ids = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def get_query_set(self) -> QuerySet:
        query_set = QuerySet(Log).all()

        start_time = _parse_date(self.data.get('start_time'))
        if start_time is not None:
            query_set = query_set.filter(create_time__gte=start_time)

        end_time = _parse_date(self.data.get('end_time'), end_of_day=True)
        if end_time is not None:
            query_set = query_set.filter(create_time__lte=end_time)

        user = self.data.get('user')
        if user:
            query_set = query_set.filter(user__username__icontains=user)

        status = self.data.get('status')
        if status:
            try:
                query_set = query_set.filter(status=int(status))
            except (TypeError, ValueError):
                pass

        ip_address = self.data.get('ip_address')
        if ip_address:
            query_set = query_set.filter(ip_address__icontains=ip_address)

        menu_list = _parse_list(self.data.get('menu'))
        if len(menu_list) > 0:
            # 选中的是归并后的菜单，这里展开成数据库中实际存在的写法
            raw_menu_list = set(menu_list)
            for raw_menu, canonical in MENU_CANONICAL.items():
                if canonical in menu_list:
                    raw_menu_list.add(raw_menu)
            query_set = query_set.filter(menu__in=list(raw_menu_list))

        workspace_ids = _parse_list(self.data.get('workspace_ids'))
        if len(workspace_ids) > 0:
            query_set = query_set.filter(workspace_id__in=workspace_ids)

        return query_set.order_by('-create_time')

    @staticmethod
    def to_record(log: Log) -> dict:
        user = log.user if isinstance(log.user, dict) else {'username': str(log.user)}
        return {
            'id': str(log.id),
            'menu': canonical_menu(log.menu),
            'menu_label': get_menu_label(canonical_menu(log.menu)),
            'operate': str(_(log.operate)) if log.operate else log.operate,
            'operation_object': log.operation_object or {},
            'user': user,
            'status': log.status,
            'ip_address': log.ip_address,
            'details': log.details or {},
            'workspace_id': log.workspace_id,
            'workspace_name': '默认工作空间' if log.workspace_id in (None, '', 'default') else log.workspace_id,
            'create_time': log.create_time,
        }

    def page(self, current_page: int, page_size: int):
        self.is_valid(raise_exception=True)
        return page_search(current_page, page_size, self.get_query_set(), self.to_record)

    @staticmethod
    def menu_options() -> list:
        raw_menus = list(QuerySet(Log).values_list('menu', flat=True).distinct())
        menus = {canonical_menu(menu) for menu in raw_menus if menu}
        menus.update(canonical_menu(menu) for menu in KNOWN_MENUS)
        return sorted(
            [{'menu': menu, 'menu_label': get_menu_label(menu)} for menu in menus if menu],
            key=lambda item: item['menu_label'],
        )

    def export(self):
        self.is_valid(raise_exception=True)

        def stream_response():
            workbook = openpyxl.Workbook(write_only=True)
            worksheet = workbook.create_sheet(title='Sheet1')
            worksheet.append(EXPORT_HEADERS['zh' if is_zh_language() else 'en'])
            for log in self.get_query_set().iterator():
                record = self.to_record(log)
                operation_object = record.get('operation_object') or {}
                object_name = operation_object.get('name') if isinstance(operation_object, dict) else None
                operate = record.get('operate') or ''
                if object_name:
                    operate = f'{operate}【{object_name}】'
                worksheet.append([
                    _cell_value(record.get('menu_label')),
                    _cell_value(operate),
                    _cell_value((record.get('user') or {}).get('username')),
                    ('成功' if is_zh_language() else 'Success')
                    if record.get('status') == 200
                    else ('失败' if is_zh_language() else 'Failed'),
                    _cell_value(record.get('ip_address')),
                    _cell_value(timezone.localtime(record.get('create_time')).strftime('%Y-%m-%d %H:%M:%S')
                                if record.get('create_time') else ''),
                ])
            output = BytesIO()
            workbook.save(output)
            output.seek(0)
            yield output.getvalue()
            output.close()
            workbook.close()

        response = StreamingHttpResponse(
            stream_response(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="operate_log.xlsx"'
        return response
