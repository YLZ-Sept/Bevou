# coding=utf-8
"""
    @project: MaxKB
    @file: chat_user.py
    @desc: 对话用户 / 用户组管理
"""
import json
import re

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.db.search import page_search
from common.exception.app_exception import AppApiException
from common.utils.common import password_encrypt
from common.utils.rsa_util import decrypt
from system_manage.models import ChatUser, UserGroup, UserGroupRelation

PASSWORD_SPECIAL_CHARS = '!"#$%&\\\'()*+,-./:;<=>?@[\\\\]^_`{|}~'

PASSWORD_REGEX = re.compile(
    r"^"
    r"(?=.*[a-z])"
    r"(?=.*[A-Z])"
    r"(?=.*\d)"
    r"(?=.*[" + re.escape(PASSWORD_SPECIAL_CHARS) + r"])"
    r"[a-zA-Z0-9" + re.escape(PASSWORD_SPECIAL_CHARS) + r"]{6,20}"
    r"$"
)


def _check_password(password: str):
    if not password or not PASSWORD_REGEX.match(password):
        raise AppApiException(
            500,
            _('The password must be 6-20 characters long and must be a combination of letters, numbers, and special characters.'),
        )


def _decrypt_password(password, encrypted=False):
    if encrypted and password:
        try:
            return decrypt(password)
        except Exception:
            raise AppApiException(500, _('Invalid encrypted data'))
    return password


def _group_mapping(user_ids) -> dict:
    """user_id -> [{'id': group_id, 'name': group_name}]"""
    mapping = {}
    relations = UserGroupRelation.objects.filter(user_id__in=user_ids).select_related('group')
    for relation in relations:
        mapping.setdefault(str(relation.user_id), []).append(
            {'id': str(relation.group_id), 'name': relation.group.name}
        )
    return mapping


def _user_record(user: ChatUser, groups=None) -> dict:
    groups = groups or []
    return {
        'id': str(user.id),
        'username': user.username,
        'nick_name': user.nick_name,
        'email': user.email or '',
        'phone': user.phone or '',
        'source': user.source,
        'is_active': user.is_active,
        'create_time': user.create_time,
        'user_group_ids': [group['id'] for group in groups],
        'user_group_names': [group['name'] for group in groups],
    }


class ChatUserSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, max_length=64)
    nick_name = serializers.CharField(required=False, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=1024)
    encrypted = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    user_group_ids = serializers.ListField(child=serializers.CharField(), required=False)

    @staticmethod
    def list_users() -> list:
        users = QuerySet(ChatUser).order_by('username')
        return [
            {'id': str(user.id), 'username': user.username, 'nick_name': user.nick_name}
            for user in users
        ]

    def page(self, current_page: int, page_size: int, params: dict):
        self.is_valid(raise_exception=True)
        keyword = params.get('username_or_nickname') or params.get('keyword')
        query_set = QuerySet(ChatUser).all()
        if keyword:
            query_set = query_set.filter(Q(username__icontains=keyword) | Q(nick_name__icontains=keyword))
        if params.get('is_active') is not None and str(params.get('is_active')) != '':
            query_set = query_set.filter(is_active=str(params.get('is_active')).lower() in ('true', '1'))
        query_set = query_set.order_by('-create_time')

        result = page_search(current_page, page_size, query_set, lambda user: user)
        group_mapping = _group_mapping([str(user.id) for user in result.get('records')])
        result['records'] = [
            _user_record(user, group_mapping.get(str(user.id)))
            for user in result.get('records')
        ]
        return result

    @transaction.atomic
    def save(self):
        self.is_valid(raise_exception=True)
        data = self.initial_data
        username = (data.get('username') or '').strip()
        if not (4 <= len(username) <= 64):
            raise AppApiException(500, _('Username must be 4-64 characters long'))
        if QuerySet(ChatUser).filter(username=username).exists():
            raise AppApiException(500, _('Username already exists'))
        nick_name = (data.get('nick_name') or '').strip()
        if not nick_name:
            raise AppApiException(500, _('Nick name is required'))
        if QuerySet(ChatUser).filter(nick_name=nick_name).exists():
            raise AppApiException(500, _('Nick name already exists'))

        password = _decrypt_password(data.get('password'), data.get('encrypted'))
        _check_password(password)

        user = ChatUser(
            username=username,
            nick_name=nick_name,
            email=data.get('email') or '',
            phone=data.get('phone') or '',
            password=password_encrypt(password),
            source='LOCAL',
            is_active=bool(data.get('is_active', True)),
        )
        user.save()
        self._save_groups(user.id, data.get('user_group_ids') or [])
        return _user_record(user, _group_mapping([str(user.id)]).get(str(user.id)))

    @staticmethod
    def _save_groups(user_id, group_ids):
        if group_ids is None:
            return
        valid_group_ids = set(
            str(group.id) for group in QuerySet(UserGroup).filter(id__in=group_ids)
        )
        UserGroupRelation.objects.filter(user_id=user_id).delete()
        for group_id in valid_group_ids:
            UserGroupRelation(user_id=user_id, group_id=group_id).save()

    @transaction.atomic
    def edit(self, user_id: str):
        self.is_valid(raise_exception=True)
        data = self.initial_data
        user = QuerySet(ChatUser).filter(id=user_id).first()
        if user is None:
            raise AppApiException(500, _('User not found'))

        nick_name = (data.get('nick_name') or '').strip()
        if nick_name and nick_name != user.nick_name:
            if QuerySet(ChatUser).filter(nick_name=nick_name).exclude(id=user_id).exists():
                raise AppApiException(500, _('Nick name already exists'))
            user.nick_name = nick_name
        if 'email' in data:
            user.email = data.get('email') or ''
        if 'phone' in data:
            user.phone = data.get('phone') or ''
        if 'is_active' in data:
            user.is_active = bool(data.get('is_active'))
        user.save()
        if 'user_group_ids' in data:
            self._save_groups(user.id, data.get('user_group_ids') or [])
        return _user_record(user, _group_mapping([str(user.id)]).get(str(user.id)))

    def re_password(self, user_id: str):
        self.is_valid(raise_exception=True)
        user = QuerySet(ChatUser).filter(id=user_id).first()
        if user is None:
            raise AppApiException(500, _('User not found'))
        data = dict(self.initial_data)
        if data.get('encryptedData'):
            try:
                data = json.loads(decrypt(data.get('encryptedData')))
            except Exception:
                raise AppApiException(500, _('Invalid encrypted data'))
        password = data.get('password')
        _check_password(password)
        user.password = password_encrypt(password)
        user.save(update_fields=['password', 'update_time'])
        return True

    @staticmethod
    def delete(user_id: str):
        ChatUser.objects.filter(id=user_id).delete()
        return True

    @staticmethod
    def batch_delete(user_id_list):
        if not isinstance(user_id_list, list):
            raise AppApiException(500, _('Invalid parameter'))
        ChatUser.objects.filter(id__in=user_id_list).delete()
        return True

    @transaction.atomic
    def batch_add_group(self):
        self.is_valid(raise_exception=True)
        data = self.initial_data
        user_ids = data.get('ids') or []
        group_ids = data.get('user_group_ids') or []
        is_append = bool(data.get('is_append', True))
        valid_group_ids = [str(group.id) for group in QuerySet(UserGroup).filter(id__in=group_ids)]
        for user_id in user_ids:
            if not is_append:
                # 覆盖语义：先清空已有分组
                UserGroupRelation.objects.filter(user_id=user_id).delete()
            existing = set(
                str(relation.group_id) for relation in UserGroupRelation.objects.filter(user_id=user_id)
            )
            for group_id in valid_group_ids:
                if group_id not in existing:
                    UserGroupRelation(user_id=user_id, group_id=group_id).save()
        return True

    @staticmethod
    def sync_types() -> list:
        return []

    @staticmethod
    def sync(sync_type: str):
        # 社区版不支持从外部平台同步对话用户
        raise AppApiException(500, _('User synchronization is not supported'))


class UserGroupSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    name = serializers.CharField(required=False, max_length=150)
    user_ids = serializers.ListField(child=serializers.CharField(), required=False)

    @staticmethod
    def list_groups() -> list:
        return [
            {'id': str(group.id), 'name': group.name}
            for group in QuerySet(UserGroup).order_by('id')
        ]

    def save(self):
        self.is_valid(raise_exception=True)
        data = self.initial_data
        name = (data.get('name') or '').strip()
        if not name:
            raise AppApiException(500, _('Group name is required'))
        group_id = data.get('id')
        if group_id:
            group = QuerySet(UserGroup).filter(id=group_id).first()
            if group is None:
                raise AppApiException(500, _('Group not found'))
            if QuerySet(UserGroup).filter(name=name).exclude(id=group_id).exists():
                raise AppApiException(500, _('Group name already exists'))
            group.name = name
            group.save()
        else:
            if QuerySet(UserGroup).filter(name=name).exists():
                raise AppApiException(500, _('Group name already exists'))
            group = UserGroup(name=name)
            group.save()
        return {'id': str(group.id), 'name': group.name}

    @staticmethod
    def delete(group_id: str):
        UserGroup.objects.filter(id=group_id).delete()
        return True

    def add_member(self, group_id: str):
        self.is_valid(raise_exception=True)
        if not QuerySet(UserGroup).filter(id=group_id).exists():
            raise AppApiException(500, _('Group not found'))
        user_ids = self.initial_data.get('user_ids') or []
        existing = set(
            str(relation.user_id) for relation in UserGroupRelation.objects.filter(group_id=group_id)
        )
        for user_id in user_ids:
            if user_id not in existing and QuerySet(ChatUser).filter(id=user_id).exists():
                UserGroupRelation(user_id=user_id, group_id=group_id).save()
        return True

    def remove_member(self, group_id: str):
        self.is_valid(raise_exception=True)
        user_ids = self.initial_data.get('user_ids') or []
        UserGroupRelation.objects.filter(group_id=group_id, user_id__in=user_ids).delete()
        return True

    @staticmethod
    def page_users(group_id: str, current_page: int, page_size: int, params: dict):
        keyword = params.get('username_or_nickname') or params.get('keyword')
        user_ids = UserGroupRelation.objects.filter(group_id=group_id).values_list('user_id', flat=True)
        query_set = QuerySet(ChatUser).filter(id__in=list(user_ids))
        if keyword:
            query_set = query_set.filter(Q(username__icontains=keyword) | Q(nick_name__icontains=keyword))
        query_set = query_set.order_by('-create_time')

        result = page_search(current_page, page_size, query_set, lambda user: user)
        group_mapping = _group_mapping([str(user.id) for user in result.get('records')])
        result['records'] = [
            _user_record(user, group_mapping.get(str(user.id)))
            for user in result.get('records')
        ]
        return result
