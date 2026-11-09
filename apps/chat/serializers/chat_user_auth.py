# coding=utf-8
"""
    @project: MaxKB
    @file: chat_user_auth.py
    @desc: 对话用户本地账号登录（二开）
"""
import json

from django.core.cache import cache
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from application.models import ApplicationAccessToken, ChatUserType
from common.auth.common import ChatUserToken, ChatAuthentication, FileToken
from common.constants.authentication_type import AuthenticationType
from common.constants.cache_version import Cache_Version
from common.exception.app_exception import AppApiException, NotFound404
from common.utils.common import password_verify
from common.utils.rsa_util import decrypt
from system_manage.models import ChatUser

system_version, system_get_key = Cache_Version.SYSTEM.value


def _record_login_fail(username: str):
    key = system_get_key(f"chat_{username}")
    try:
        return cache.incr(key, 1, version=system_version)
    except ValueError:
        cache.set(key, 1, timeout=600, version=system_version)
        return 1


def _clear_login_fail(username: str):
    cache.delete(system_get_key(f"chat_{username}"), version=system_version)


class ChatUserLoginSerializer:
    """对话用户登录"""

    @staticmethod
    def _parse_data(request_data) -> dict:
        data = dict(request_data)
        if data.get('encryptedData'):
            try:
                return json.loads(decrypt(data.get('encryptedData')))
            except Exception:
                raise AppApiException(500, _('Invalid encrypted data'))
        return data

    @staticmethod
    def _get_access_token(access_token: str) -> ApplicationAccessToken:
        application_access_token = QuerySet(ApplicationAccessToken).filter(access_token=access_token).first()
        if application_access_token is None or not application_access_token.is_active:
            raise NotFound404(404, _('Invalid access_token'))
        if not application_access_token.authentication:
            raise AppApiException(500, _('Authentication is not enabled'))
        return application_access_token

    def login(self, access_token: str, request_data):
        application_access_token = self._get_access_token(access_token)
        data = self._parse_data(request_data)
        username = data.get('username') or ''
        password = data.get('password') or ''
        captcha = data.get('captcha') or ''

        authentication_value = application_access_token.authentication_value or {}
        login_value = authentication_value.get('login_value', ['LOCAL'])
        if login_value and 'LOCAL' not in login_value:
            raise AppApiException(500, _('Local account login is not enabled'))
        max_attempts = authentication_value.get('max_attempts', 1)

        # 需要验证码时校验
        fail_count = cache.get(system_get_key(f"chat_{username}"), version=system_version) or 0
        need_captcha = max_attempts != -1 and (max_attempts <= 0 or fail_count >= max_attempts)
        if need_captcha:
            if not captcha:
                raise AppApiException(1005, _('Captcha is required'))
            captcha_key = Cache_Version.CAPTCHA.get_key(captcha=f"chat_{username}")
            cached_captcha = cache.get(captcha_key, version=Cache_Version.CAPTCHA.get_version())
            if cached_captcha is None or captcha.lower() != cached_captcha:
                _record_login_fail(username)
                raise AppApiException(1005, _('Captcha code error or expiration'))
            cache.delete(captcha_key, version=Cache_Version.CAPTCHA.get_version())

        chat_user = QuerySet(ChatUser).filter(username=username).first()
        if chat_user is None or not password_verify(password, chat_user.password):
            _record_login_fail(username)
            raise AppApiException(500, _('The username or password is incorrect'))
        if not chat_user.is_active:
            raise AppApiException(1005, _('The user has been disabled, please contact the administrator!'))

        _clear_login_fail(username)
        chat_user_token = ChatUserToken(
            application_access_token.application_id,
            str(chat_user.id),
            access_token,
            AuthenticationType.CHAT_USER,
            ChatUserType.CHAT_USER,
            str(chat_user.id),
            ChatAuthentication('LOCAL'),
        )
        return {
            'token': chat_user_token.to_token(),
            'f_token': FileToken(
                str(chat_user.id),
                AuthenticationType.CHAT_USER.value,
                application_id=str(application_access_token.application_id),
            ).to_token(),
        }
