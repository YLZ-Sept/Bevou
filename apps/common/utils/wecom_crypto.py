# coding=utf-8
"""
    @project: MaxKB
    @file: wecom_crypto.py
    @desc: 企业微信回调消息加解密（WXBizMsgCrypt 兼容实现）
"""
import base64
import hashlib
import hmac
import os
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class WeComCrypto:
    def __init__(self, token: str, encoding_aes_key: str, receive_id: str = ''):
        self.token = token or ''
        self.receive_id = receive_id or ''
        self.key = base64.b64decode((encoding_aes_key or '') + '=')

    def signature(self, timestamp, nonce, encrypt) -> str:
        items = sorted([self.token, str(timestamp), str(nonce), encrypt])
        return hashlib.sha1(''.join(items).encode('utf-8')).hexdigest()

    def verify(self, msg_signature, timestamp, nonce, encrypt) -> bool:
        return hmac.compare_digest(self.signature(timestamp, nonce, encrypt), msg_signature or '')

    def decrypt(self, encrypt_b64: str) -> str:
        data = base64.b64decode(encrypt_b64)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.key[:16]))
        decryptor = cipher.decryptor()
        plain = decryptor.update(data) + decryptor.finalize()
        # PKCS#7，块大小 32
        pad = plain[-1]
        plain = plain[:-pad]
        msg_len = struct.unpack('>I', plain[16:20])[0]
        return plain[20:20 + msg_len].decode('utf-8')

    def encrypt(self, msg: str) -> str:
        msg_bytes = msg.encode('utf-8')
        payload = os.urandom(16) + struct.pack('>I', len(msg_bytes)) + msg_bytes + self.receive_id.encode('utf-8')
        pad = 32 - (len(payload) % 32)
        payload += bytes([pad]) * pad
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.key[:16]))
        encryptor = cipher.encryptor()
        return base64.b64encode(encryptor.update(payload) + encryptor.finalize()).decode()
