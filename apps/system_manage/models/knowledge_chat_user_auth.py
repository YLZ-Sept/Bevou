# coding=utf-8
"""
    @project: MaxKB
    @file: knowledge_chat_user_auth.py
    @desc: 知识库对话用户/用户组授权（二开）
"""
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin


class KnowledgeChatUserAuthorize(AppModelMixin):
    """
    知识库检索授权：
    - 某知识库没有任何记录时，视为不限制
    - 一旦存在记录，仅记录中的对话用户/用户组可检索该知识库
    """
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False,
                          verbose_name='主键id')
    workspace_id = models.CharField(max_length=64, default='default', db_index=True)
    knowledge_id = models.UUIDField(max_length=128, db_index=True)
    subject_type = models.CharField(max_length=16, db_index=True, verbose_name='授权对象类型')
    subject_id = models.CharField(max_length=64, db_index=True, verbose_name='授权对象id')
    is_auth = models.BooleanField(default=True, verbose_name='是否授权')

    class Meta:
        db_table = 'knowledge_chat_user_authorize'
        unique_together = ('knowledge_id', 'subject_type', 'subject_id')
