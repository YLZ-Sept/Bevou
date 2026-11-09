# coding=utf-8
"""
    @project: MaxKB
    @file: platform_callback.py
    @desc: 第三方平台回调消息处理（企业微信应用 / 企业微信智能机器人 / 钉钉）
"""
import base64
import hashlib
import hmac
import json
import random
import time
import xml.etree.ElementTree as ET

import requests
from django.db.models import QuerySet
from django.http import Http404, HttpResponse, JsonResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from common.utils.logger import maxkb_logger
from common.utils.wecom_crypto import WeComCrypto
from system_manage.models import ApplicationPlatformConfig

FALLBACK_ANSWER = '抱歉，应用暂时无法回答该消息，请稍后再试。'
UNSUPPORTED_ANSWER = '暂不支持该消息类型，请发送文字消息。'


def _get_config(application_id: str, platform: str):
    row = QuerySet(ApplicationPlatformConfig).filter(
        application_id=application_id, platform=platform, is_active=True
    ).first()
    return dict(row.meta) if row is not None else None


def _cdata(value: str) -> str:
    return '<![CDATA[' + str(value).replace(']]>', ']]&gt;') + ']]>'


def _generate_answer(application_id: str, platform: str, from_user: str, content: str) -> str:
    from common.utils.common import get_random_chars, password_encrypt
    from system_manage.models import ChatUser
    from chat.serializers.chat import OpenAIChatSerializer

    username = f'{platform}_{from_user}'[:150]
    nick_name = f'{from_user}@{platform}'[:150]
    chat_user = QuerySet(ChatUser).filter(username=username).first()
    if chat_user is None:
        try:
            chat_user = ChatUser(
                username=username,
                nick_name=nick_name,
                password=password_encrypt('Th@' + get_random_chars(8) + '1'),
                source=platform,
                is_active=True,
            )
            chat_user.save()
        except Exception:
            chat_user = QuerySet(ChatUser).filter(username=username).first()
    if chat_user is None:
        return FALLBACK_ANSWER
    try:
        response = OpenAIChatSerializer(data={
            'application_id': application_id,
            'chat_user_id': str(chat_user.id),
            'chat_user_type': 'CHAT_USER',
            'ip_address': '0.0.0.0',
            'source': {'type': 'ONLINE'},
        }).chat({
            'messages': [{'role': 'user', 'content': content}],
            'stream': False,
        })
        data = json.loads(response.content.decode('utf-8'))
        answer = data.get('choices', [{}])[0].get('message', {}).get('content')
        return answer or FALLBACK_ANSWER
    except Exception as e:
        maxkb_logger.exception(f'{platform} bot answer failed: {e}')
        return FALLBACK_ANSWER


def _build_wecom_reply(crypto: WeComCrypto, from_user: str, to_user: str, answer: str) -> HttpResponse:
    reply_xml = (
        '<xml>'
        f'<ToUserName>{_cdata(from_user)}</ToUserName>'
        f'<FromUserName>{_cdata(to_user)}</FromUserName>'
        f'<CreateTime>{int(time.time())}</CreateTime>'
        '<MsgType><![CDATA[text]]></MsgType>'
        f'<Content>{_cdata(answer)}</Content>'
        '</xml>'
    )
    encrypted = crypto.encrypt(reply_xml)
    timestamp = str(int(time.time()))
    nonce = str(random.randint(100000, 999999))
    signature = crypto.signature(timestamp, nonce, encrypted)
    response_xml = (
        '<xml>'
        f'<Encrypt>{_cdata(encrypted)}</Encrypt>'
        f'<MsgSignature>{_cdata(signature)}</MsgSignature>'
        f'<TimeStamp>{timestamp}</TimeStamp>'
        f'<Nonce>{_cdata(nonce)}</Nonce>'
        '</xml>'
    )
    return HttpResponse(response_xml, content_type='application/xml')


def _wecom_get(request, meta: dict, receive_id: str):
    echostr = request.query_params.get('echostr')
    if not echostr:
        return HttpResponse(status=400)
    crypto = WeComCrypto(meta.get('token'), meta.get('encoding_aes_key'), receive_id)
    msg_signature = request.query_params.get('msg_signature')
    timestamp = request.query_params.get('timestamp')
    nonce = request.query_params.get('nonce')
    if crypto.verify(msg_signature, timestamp, nonce, echostr):
        return HttpResponse(crypto.decrypt(echostr), content_type='text/plain')
    return HttpResponse(status=403)


def _wecom_post(request, meta: dict, application_id: str, platform: str, receive_id: str):
    crypto = WeComCrypto(meta.get('token'), meta.get('encoding_aes_key'), receive_id)
    try:
        root = ET.fromstring(request.body.decode('utf-8'))
    except ET.ParseError:
        return HttpResponse(status=400)
    encrypt = root.findtext('Encrypt')
    msg_signature = request.query_params.get('msg_signature')
    timestamp = request.query_params.get('timestamp')
    nonce = request.query_params.get('nonce')
    if not encrypt or not crypto.verify(msg_signature, timestamp, nonce, encrypt):
        return HttpResponse(status=403)
    try:
        message = ET.fromstring(crypto.decrypt(encrypt))
    except Exception:
        return HttpResponse(status=400)

    from_user = message.findtext('FromUserName') or ''
    to_user = message.findtext('ToUserName') or ''
    msg_type = message.findtext('MsgType') or ''
    content = (message.findtext('Content') or '').strip()

    if msg_type == 'event':
        # 关注/进入应用等事件无需回复
        return HttpResponse('', content_type='text/plain')
    if msg_type != 'text' or not content:
        return _build_wecom_reply(crypto, from_user, to_user, UNSUPPORTED_ANSWER)

    answer = _generate_answer(application_id, platform, from_user, content)
    return _build_wecom_reply(crypto, from_user, to_user, answer)


def _dingtalk_verify(request, meta: dict) -> bool:
    timestamp = request.headers.get('timestamp') or request.headers.get('Timestamp')
    sign = request.headers.get('sign') or request.headers.get('Sign')
    secret = meta.get('client_secret') or ''
    if not timestamp or not sign or not secret:
        # 未提供签名头时不阻断（回调地址本身即凭据）
        return True
    string_to_sign = f'{timestamp}\n{secret}'.encode('utf-8')
    expected = base64.b64encode(
        hmac.new(secret.encode('utf-8'), string_to_sign, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, sign)


def _dingtalk_post(request, meta: dict, application_id: str):
    if not _dingtalk_verify(request, meta):
        return HttpResponse(status=403)
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    # 支持加密回调（配置了 token/EncodingAESKey 时）
    if isinstance(data, dict) and data.get('encrypt'):
        token = meta.get('token')
        aes_key = meta.get('encoding_aes_key')
        if not token or not aes_key:
            return HttpResponse(status=400)
        crypto = WeComCrypto(token, aes_key, meta.get('client_id') or '')
        try:
            data = json.loads(crypto.decrypt(data.get('encrypt')))
        except Exception:
            return HttpResponse(status=400)

    content = ((data.get('text') or {}).get('content') or '').strip()
    if not content:
        # 事件或非文本消息
        return HttpResponse('', status=200)

    sender = data.get('senderStaffId') or data.get('senderNick') or 'dingtalk_user'
    answer = _generate_answer(application_id, 'dingtalk', sender, content)

    session_webhook = data.get('sessionWebhook')
    if session_webhook:
        try:
            requests.post(
                session_webhook,
                json={'msgtype': 'text', 'text': {'content': answer}},
                timeout=10,
            )
            return HttpResponse('', status=200)
        except Exception as e:
            maxkb_logger.exception(f'dingtalk sessionWebhook reply failed: {e}')
    return JsonResponse({'msgtype': 'text', 'text': {'content': answer}}, status=200)


class PlatformCallbackView(APIView):
    """回调由平台签名校验，不使用登录态；沿用全局 AnonymousAuthentication"""

    def get(self, request: Request, platform: str, application_id: str):
        meta = _get_config(application_id, platform)
        if meta is None:
            raise Http404
        if platform in ('wecomBot', 'wecom'):
            receive_id = meta.get('app_id', '') if platform == 'wecom' else ''
            return _wecom_get(request, meta, receive_id)
        return HttpResponse(status=404)

    def post(self, request: Request, platform: str, application_id: str):
        meta = _get_config(application_id, platform)
        if meta is None:
            raise Http404
        if platform in ('wecomBot', 'wecom'):
            receive_id = meta.get('app_id', '') if platform == 'wecom' else ''
            return _wecom_post(request, meta, application_id, platform, receive_id)
        if platform == 'dingtalk':
            return _dingtalk_post(request, meta, application_id)
        return HttpResponse(status=404)
