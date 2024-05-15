'''
    ソラコム認証用モジュール

    2024/5/15 t.odaka 

'''
import os

from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG, INFO
import time
from datetime import datetime

import json, ast
import urllib.request

import LogUtils as LU

SCRIPT_NAME = os.path.basename(__file__)
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__)) # スクリプトのあるディレクトリの絶対パス

# logging
LOGGER = getLogger(os.path.basename(__file__))
LOG_FMT = "[%(name)s] %(asctime)s %(levelname)s %(lineno)s %(message)s"

LOGGER = LU.setScreenLogger(LOGGER, LOG_FMT, 'debug') # develop

'''
    Access Tokenの取得

    SAM ユーザーの API キーと API トークンを発行する
    https://users.soracom.io/ja-jp/tools/api/key-and-token/#sam-%e3%83%a6%e3%83%bc%e3%82%b6%e3%83%bc%e3%81%ae-api-%e3%82%ad%e3%83%bc%e3%81%a8-api-%e3%83%88%e3%83%bc%e3%82%af%e3%83%b3%e3%82%92%e7%99%ba%e8%a1%8c%e3%81%99%e3%82%8b

'''
def getToken(url, auth_key_id, auth_key):

    _d = dict()
    _d["authKeyId"] = auth_key_id
    _d["authKey"] = auth_key

    _method = 'POST'
    _headers = { 'Content-Type': 'application/json; charset=utf-8' }
    _body = json.dumps(_d).encode()
    req = urllib.request.Request(
        url = url, 
        data = _body, 
        method = _method,
        headers = _headers 
    )
    try:
        with urllib.request.urlopen(req) as res:
            # https://qiita.com/krang/items/119bff51c30d3b7637dd
            #内容のbyte型への変換 type:byte型
            data = res.read()
            #内容のbite型→文字列型へのデコード type:str型
            res = data.decode("utf-8")
            # 文字列型→辞書型への変換 type:dictionary型
            _rb = ast.literal_eval(res)

        if 'token' in _rb:
            return _rb['apiKey'], _rb["token"], _rb['operatorId'], _rb['userName']
        
    except urllib.error.HTTPError as err:
        LOGGER.error('urllib.error.HTTPError. code {}'.format(err.code))
    except urllib.error.URLError as err:
        LOGGER.error('urllib.error.URLError. reason {}'.format(err.reason))

    return None


'''
    Tokenの無効化（API呼び出し終了後のトークンの無効化）

    API キーと API トークンを無効化する
    https://users.soracom.io/ja-jp/tools/api/key-and-token/#api-%e3%82%ad%e3%83%bc%e3%81%a8-api-%e3%83%88%e3%83%bc%e3%82%af%e3%83%b3%e3%82%92%e7%84%a1%e5%8a%b9%e5%8c%96%e3%81%99%e3%82%8b

'''
def revokeToken(api_key, token):
    url = 'https://api.soracom.io/v1/auth/logout'

    _method = 'POST'
    _headers = { 
        'X-Soracom-API-Key' : api_key,
        'X-Soracom-Token' : token
        }
    _body = None

    req = urllib.request.Request(
        url = url, 
        data = _body, 
        method = _method,
        headers = _headers 
    )
    try:
        with urllib.request.urlopen(req) as res:
            #内容のbyte型への変換 type:byte型
            data = res.read()
            #内容のbite型→文字列型へのデコード type:str型
            res = data.decode("utf-8")
            if len(res) > 0:
                # 文字列型→辞書型への変換 type:dictionary型
                _dict = ast.literal_eval(res)
            else:
                # 正常終了
                _dict = None

            return _dict

    except urllib.error.HTTPError as err:
        LOGGER.error('urllib.error.HTTPError. code {}'.format(err.code))
    except urllib.error.URLError as err:
        LOGGER.error('urllib.error.URLError. reason {}'.format(err.reason))

    # 正常終了
    return None


'''
	main：関数テスト用

    
'''
if __name__ == "__main__":
    LOGGER.info('script start')
    start_time = time.time()

    auth_key_id = os.environ['SORACOM_AUTH_KEY_ID']
    auth_key = os.environ['SORACOM_AUTH_KEY']

    LOGGER.debug(auth_key_id)
    LOGGER.debug(auth_key)

    # accessトークンの取得
    url = 'https://api.soracom.io/v1/auth'
    akey, token, oid, unm = getToken(url, auth_key_id, auth_key)
    if not token == None:
        LOGGER.debug(akey)
        LOGGER.debug(oid)
        LOGGER.debug(unm)
        LOGGER.debug(token)
    else:
        LOGGER.debug("no token")

    if not token == None:
        # apiキーとトークンの無効化
        revokeToken(akey, token)
        LOGGER.debug("token was revoked.")

    elapsed_time = time.time() - start_time
    LOGGER.info('script end')
    LOGGER.info('elapsed time : {} [sec]'.format(str(elapsed_time)))
