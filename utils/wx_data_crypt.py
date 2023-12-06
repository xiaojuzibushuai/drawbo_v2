# -*- coding: utf-8 -*-
import base64
import json
from Crypto.Cipher import AES


class WxDataCrypt:
    def __init__(self, app_id, session_key):
        self.app_id = app_id
        self.session_key = session_key

    def decrypt(self, encrypted_data, iv):
        # base64 decode
        dc_sk = base64.b64decode(self.session_key)
        dc_data = base64.b64decode(encrypted_data)
        dc_iv = base64.b64decode(iv)

        cipher = AES.new(dc_sk, AES.MODE_CBC, dc_iv)
        decrypted = json.loads(self._unpad(cipher.decrypt(dc_data)))
        if decrypted['watermark']['appid'] != self.app_id:
            raise Exception('Invalid Buffer')
        return decrypted

    def _unpad(self, s):
        print(s)
        if isinstance(s, bytes):
            print(s.decode('utf8'))
        return s[:-ord(s[len(s) - 1:])]


if __name__ == '__main__':
    wdc = WxDataCrypt('wx825a2ccae52d33b7', 'DlpVa3DD3KZS9Bh8nliMww==')
    res = wdc.decrypt('hP5VZVXuEakDpk3jrzWocOU6yQsRrmsiPZTrEAIxsDqdjNeJU6PBvyoYnzVNXnUX6IBC8/N9M597cu95xIb2f+jkxX/Rc2zM7TbOss2ODXoCyn3ABlJzeblEIcH6mo7xzWPJr4ZKDX4IPrqoQzDxfMGSBGeiYIwm9dRrStzs2ee636PY8dTdHjAMXQiJySVTQOtBihkMs6elnm8IjXlXMQ==', 'SxwA2nLqhL5OBqWZoS6OGQ==')
    print(res)
