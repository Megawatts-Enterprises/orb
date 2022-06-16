# -*- coding: utf-8 -*-
# @Author: lnorb.com
# @Date:   2022-01-09 08:41:00
# @Last Modified by:   lnorb.com
# @Last Modified time: 2022-06-17 07:30:07

import re
import base64

from orb.misc.macaroon import Macaroon
from orb.misc.sec_rsa import *


class MacaroonSecure:
    def __init__(self, macaroon_secure):
        self.macaroon_secure = macaroon_secure

    @staticmethod
    def init_from_encrypted(text):
        return MacaroonSecure(text)

    @staticmethod
    def init_from_plain(bin_data):
        _, pub = get_sec_keys()
        encrypted = encrypt_long(bin_data, pub, True)
        return MacaroonSecure(encrypted)

    # @staticmethod
    # def init_from_not_sure(data):
    #     if type(data) is str:
    #         data = data.encode()
    #     # try decrypting it, if that doesn't work
    #     try:
    #         mac = MacaroonSecure.as_plain_macaroon(data)
    #         return mac
    #     except:
    #         pass
    #     mac = Macaroon.init_from_not_sure(data.decode())
    #     return MacaroonSecure.init_from_plain(mac.macaroon.encode())

    def as_plain_macaroon(self):
        priv, _ = get_sec_keys()
        plain = decrypt_long(self.macaroon_secure, priv)
        return Macaroon.init_from_not_sure(plain)
