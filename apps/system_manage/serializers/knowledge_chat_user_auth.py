# coding=utf-8
"""
    @project: MaxKB
    @file: knowledge_chat_user_auth.py
    @desc: 知识库对话用户/用户组授权（二开）
"""
from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from knowledge.models import Knowledge
from system_manage.models import ChatUser, KnowledgeChatUserAuthorize, UserGroup, UserGroupRelation

SUBJECT_USER = 'USER'
SUBJECT_GROUP = 'GROUP'


def get_knowledge_list_of_authorized(chat_user_id, knowledge_id_list):
    """
    过滤出当前对话用户可检索的知识库：
    - 知识库未配置授权时，不限制
    - 配置授权后，仅授权用户本人或其所在用户组可检索
    """
    knowledge_ids = [str(knowledge_id) for knowledge_id in knowledge_id_list]
    if len(knowledge_ids) == 0:
        return knowledge_ids

    grants = QuerySet(KnowledgeChatUserAuthorize).filter(
        knowledge_id__in=knowledge_ids, is_auth=True
    )
    restricted = {}
    for grant in grants:
        restricted.setdefault(str(grant.knowledge_id), set()).add((grant.subject_type, grant.subject_id))
    if len(restricted) == 0:
        return knowledge_ids

    group_ids = set()
    if chat_user_id:
        group_ids = {
            str(relation.group_id)
            for relation in UserGroupRelation.objects.filter(user_id=chat_user_id)
        }

    allowed = []
    for knowledge_id in knowledge_ids:
        subjects = restricted.get(knowledge_id)
        if subjects is None:
            # 该知识库没有配置授权，不限制
            allowed.append(knowledge_id)
            continue
        if chat_user_id and (
                (SUBJECT_USER, str(chat_user_id)) in subjects or
                any((SUBJECT_GROUP, group_id) in subjects for group_id in group_ids)
        ):
            allowed.append(knowledge_id)
    return allowed


class KnowledgeChatUserAuthSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.CharField(), required=False)
    group_ids = serializers.ListField(child=serializers.CharField(), required=False)

    def info(self, knowledge_id: str):
        if not QuerySet(Knowledge).filter(id=knowledge_id).exists():
            raise AppApiException(500, _('Knowledge base not found'))
        grants = QuerySet(KnowledgeChatUserAuthorize).filter(
            knowledge_id=knowledge_id, is_auth=True
        )
        user_ids = [grant.subject_id for grant in grants if grant.subject_type == SUBJECT_USER]
        group_ids = [grant.subject_id for grant in grants if grant.subject_type == SUBJECT_GROUP]
        return {
            'restricted': len(user_ids) + len(group_ids) > 0,
            'user_ids': user_ids,
            'group_ids': group_ids,
        }

    @transaction.atomic
    def update(self, knowledge_id: str):
        self.is_valid(raise_exception=True)
        if not QuerySet(Knowledge).filter(id=knowledge_id).exists():
            raise AppApiException(500, _('Knowledge base not found'))
        data = self.initial_data
        user_ids = [uid for uid in (data.get('user_ids') or []) if uid]
        group_ids = [gid for gid in (data.get('group_ids') or []) if gid]

        valid_user_ids = {
            str(user.id) for user in QuerySet(ChatUser).filter(id__in=user_ids)
        }
        valid_group_ids = {
            str(group.id) for group in QuerySet(UserGroup).filter(id__in=group_ids)
        }

        QuerySet(KnowledgeChatUserAuthorize).filter(knowledge_id=knowledge_id).delete()
        for user_id in valid_user_ids:
            KnowledgeChatUserAuthorize(
                knowledge_id=knowledge_id, subject_type=SUBJECT_USER, subject_id=user_id, is_auth=True
            ).save()
        for group_id in valid_group_ids:
            KnowledgeChatUserAuthorize(
                knowledge_id=knowledge_id, subject_type=SUBJECT_GROUP, subject_id=group_id, is_auth=True
            ).save()
        return True
