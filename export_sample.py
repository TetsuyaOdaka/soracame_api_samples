'''
    開始終了時刻を指定して、その時間帯に記録された（複数の）イベント録画動画から、指定したインターバルで静止画をDLする。
    （例）インターバル 3分
        イベント１動画  12:00:00 - 12:10:00、イベント２動画  12:45:00 - 12:46:00
        のとき、
        イベント１ => 12:00, 12:03, 12:06, 12:09, 12:10 
        イベント２ => 12:45, 12:46
        時点の静止画をDLする。

    2024/5/15 t.odaka

    引数：   device : device id （クラウドモーション検知 “無制限” 録画ライセンスが適用されていること）
            dir : 作業ディレクトリ
            start: ダウンロード開始録画時間。フォーマット "%Y%m%d %H%M%S"の文字列
            end : ダウンロード終了録画時間。フォーマット "%Y%m%d %H%M%S"の文字列
            interval : 何秒間隔で静止画を抽出するか？
            fps : フレームレート。1秒間に静止画を何枚見るか。
            maxwidth : 解像度（横幅）の最大値

    （注記）
    (1) ソラコム公式「タイムラプス動画を作成する」
    https://users.soracom.io/ja-jp/docs/soracom-cloud-camera-services/api-examples-creating-time-lapse-video/
    と、そのサンプル（api-examples-creating-time-lapse-video.ipynb）
    https://colab.research.google.com/github/soracom-labs/sora-cam-api-examples/blob/main/creating-time-lapse-video/api-examples-creating-time-lapse-video.ipynb
    のコードを利用させていただいています。 

'''
import sys, os
import json

from logging import getLogger
from datetime import datetime, timedelta
import time, urllib, copy

## TimeZone設定
from zoneinfo import ZoneInfo

import argparse

import LogUtils as LU
import random

import soracom_auth as SA
import soracom_utils as SU

SCRIPT_NAME = os.path.basename(__file__)
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__)) # スクリプトのあるディレクトリの絶対パス

# logging
LOGGER = getLogger(os.path.basename(__file__))
LOG_FMT = "[%(name)s] %(asctime)s %(levelname)s %(lineno)s %(message)s"

LOGGER = LU.setScreenLogger(LOGGER, LOG_FMT, 'debug') # develop


# 認証情報の取得
SORACOM_AUTH_KEY_ID = os.environ['SORACOM_AUTH_KEY_ID']
SORACOM_AUTH_KEY = os.environ['SORACOM_AUTH_KEY']

TOKYO = ZoneInfo("Asia/Tokyo")

'''
    Sora-Camデバイスのエクスポート上限の取得

    Soracom APIリファレンス
    https://users.soracom.io/ja-jp/tools/api/reference/#/SoraCam/getSoraCamDeviceExportUsage
    
'''
def getSoraCamExportUsage(api_key, token, device_id):
    url = 'https://api.soracom.io/v1/sora_cam/devices/{}/exports/usage'.format(device_id)

    _method = 'GET'
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
                # https://stackoverflow.com/questions/11174024/why-do-i-get-str-object-has-no-attribute-read-when-trying-to-use-json-loa
                _dict = json.loads(res)
            else:
                _dict = None

            return _dict

    except urllib.error.HTTPError as err:
        LOGGER.error('{}: urllib.error.HTTPError. code {}. url: {}'.format(device_id, err.code, url))
    except urllib.error.URLError as err:
        LOGGER.error('{}: urllib.error.URLError. reason {}. url: {}'.format(device_id, err.reason, url))

    return None

'''
    Sora-Camデバイスの静止画イメージのエクスポート開始

    Soracom APIリファレンス
    https://users.soracom.io/ja-jp/tools/api/reference/#/SoraCam/exportSoraCamDeviceRecordedImage

'''
def getSoraCamExportImages(api_key, token, device_id, extime, wide_angle_correction=True):
    url = 'https://api.soracom.io/v1/sora_cam/devices/{}/images/exports'.format(device_id)

    _method = 'POST'
    _headers = { 
        'X-Soracom-API-Key' : api_key,
        'X-Soracom-Token' : token,
        'Content-Type'  : 'application/json'
        }
    _d = dict()
    if wide_angle_correction:
        _d["imageFilters"] = ["wide_angle_correction"]
    _d["time"] = extime

    LOGGER.debug('exporting image. device_id {}, time {} {}'.format(device_id, extime, SU.getDateTimeFromUnixTime(extime)))
#    LOGGER.debug(SU.getDateTimeFromUnixTime(extime))
#    LOGGER.debug(json.dumps(_d))

    _body = json.dumps(_d).encode()
    req = urllib.request.Request(
        url = url,
        data = _body,
        method = _method,
        headers = _headers
    )
    
    LOGGER.debug("url: {}".format(url))
    try:
        with urllib.request.urlopen(req) as res:
            #内容のbyte型への変換 type:byte型
            data = res.read()
            #内容のbite型→文字列型へのデコード type:str型
            res = data.decode("utf-8")
            if len(res) > 0:
                # https://stackoverflow.com/questions/11174024/why-do-i-get-str-object-has-no-attribute-read-when-trying-to-use-json-loa
                _dict = json.loads(res)
            else:
                _dict = None
            
            if 'exportId' in _dict:
                LOGGER.debug('Exporting mage: status {}, exportid {}'.format(_dict['status'], _dict['exportId']))

            return _dict

    except urllib.error.HTTPError as err:
        LOGGER.error('{}: urllib.error.HTTPError. code {}. url: {}, data: {}'.format(device_id, err.code, url, json.dumps(_d)))
    except urllib.error.URLError as err:
        LOGGER.error('{}: urllib.error.URLError. reason {}. url: {}, data: {}'.format(device_id, err.reason, url, json.dumps(_d)))

    return None


'''
    Sora-Camデバイスのイベント情報の取得

    Soracom APIリファレンス
    https://users.soracom.io/ja-jp/tools/api/reference/#/SoraCam/listSoraCamDeviceEventsForDevice

'''
def listSoraCamEventsForDevice(api_key, token, device_id, st_time, ed_time):
    _url = 'https://api.soracom.io/v1/sora_cam/devices/{}/events'.format(device_id)

    _method = 'GET'
    _headers = { 
        'X-Soracom-API-Key' : api_key,
        'X-Soracom-Token' : token
        }
    
    _d = dict()
    _d["device_id"] = device_id
    _d["limit"] = 10
    _d["from"] = st_time
    _d["to"] = ed_time
    _d["sort"] = 'asc'
    
    _query = urllib.parse.urlencode(_d)
    url = _url + '?' + _query
    LOGGER.debug(url)

    req = urllib.request.Request(
        url = url, 
        method = _method,
        headers = _headers 
    )
    try:
        _ret = list()
        _flg = True
        while _flg:
            with urllib.request.urlopen(req) as res:
                #内容のbyte型への変換 type:byte型
                _dt = res.read()
                #内容のbite型→文字列型へのデコード type:str型
                data = _dt.decode("utf-8")
                data = json.loads(data)
#                LOGGER.debug(data)
                if isinstance(data, list) and len(data) > 0:
                    _ret.extend(data)
                
                    _head = res.info()
                    if 'x-soracom-next-key' in _head:
                        LOGGER.debug('x-soracom-next-key exists {}'.format(_head['x-soracom-next-key']))
                        
                        _d["last_evaluated_key"] = _head['x-soracom-next-key']
                        _query = urllib.parse.urlencode(_d)
                        url = _url + '?' + _query
                        LOGGER.debug(url)

                        req = urllib.request.Request(
                            url = url, 
                            method = _method,
                            headers = _headers 
                        )
                    else:
                        _flg = False
        
#        LOGGER.debug('data length = {}'.format(len(_ret)))

        return _ret


    except urllib.error.HTTPError as err:
        LOGGER.error('{}: urllib.error.HTTPError. code {}. url: {}'.format(device_id, err.code, url))
    except urllib.error.URLError as err:
        LOGGER.error('{}: urllib.error.URLError. reason {}. url: {}'.format(device_id, err.reason, url))

    return None

'''
    Sora-Camデバイスの静止画イメージのエクスポート処理の進捗

    Soracom APIリファレンス
    https://users.soracom.io/ja-jp/tools/api/reference/#/SoraCam/listSoraCamDeviceImageExports

'''
def listSoraCamExportImages(api_key, token, device_id, exported_ids):
    url = 'https://api.soracom.io/v1/sora_cam/devices/images/exports'

#    LOGGER.debug(exported_ids)
    _method = 'GET'
    _headers = {
        'X-Soracom-API-Key' : api_key,
        'X-Soracom-Token' : token
        }

    _d = dict()
    _d["device_id"] = device_id
    _d["limit"] = len(exported_ids)
    
    _query = urllib.parse.urlencode(_d)
    _url = url + '?' + _query
    LOGGER.debug(_url)

    req = urllib.request.Request(
        url = _url,
        method = _method,
        headers = _headers
    )

    try:
        _ret = list()
        _flg = True
        _wl = copy.deepcopy(exported_ids)
        while _flg:
            with urllib.request.urlopen(req) as res:
                #内容のbyte型への変換 type:byte型
                _dt = res.read()
                #内容のbite型→文字列型へのデコード type:str型
                data = _dt.decode("utf-8")
                data = json.loads(data)
                LOGGER.debug(data)
                if isinstance(data, list) and len(data) > 0:
                    _ret.extend(data)
                    # 依頼したエクスポートの進捗が全部取得できているか？
                    for _dt in data:
                        if 'exportId' in _dt:
                            if _dt['exportId'] in _wl:
                                _wl.remove(_dt['exportId'])
                    # 依頼したエクスポートの進捗が全部取得できていなければ、'x-soracom-next-key'をつかって次ページ。
                    if len(_wl) > 0:
                        _head = res.info()
                        LOGGER.debug(_head)                       
                        if 'x-soracom-next-key' in _head:
                            LOGGER.debug('x-soracom-next-key exists {}'.format(_head['x-soracom-next-key']))                     
                            _d["last_evaluated_key"] = _head['x-soracom-next-key']
                            _query = urllib.parse.urlencode(_d)
                            _url = url + '?' + _query
                            LOGGER.debug(_url)

                            req = urllib.request.Request(
                                url = _url,
                                method = _method,
                                headers = _headers
                            )
                    else:
                        _flg = False
                              
#        LOGGER.debug('data length = {}'.format(len(_ret)))
        return _ret

    except urllib.error.HTTPError as err:
        LOGGER.error('{}: urllib.error.HTTPError. code {}. url: {}'.format(device_id, err.code, _url))
    except urllib.error.URLError as err:
        LOGGER.error('{}: urllib.error.URLError. reason {}. url: {}'.format(device_id, err.reason, _url))

    return None

'''
    Sora-Camの静止画ダウンロードの進捗

    listSoraCamExportImagesを指数バックオフで待つ処理をたくさん書くのが面倒なので関数化した

'''
def waitSoraCamExportImages(api_key, token, device_id, exported_ids, MAX_ATTEMPT=7):
#    LOGGER.debug(exported_ids)
    num_of_images = len(exported_ids)
    flag = True
    completed = True
    backoff = 1
    while flag:
        # ダウンロードの進捗。
        _l = listSoraCamExportImages(api_key, token, device_id, exported_ids)
        if isinstance(_l, list):
            _nc = 0
            for _d in _l:
                if 'exportId' in _d:
                    if _d['exportId'] in exported_ids:
                        _nc += 1
                        # ダウンロード可能な状態
                        if _d['status'] == 'completed':
                            LOGGER.debug("Image export completed. device_id:{}, status:{}, export_id:{}".format(device_id, _d['status'], _d['exportId']))
                        # ダウンロード不可能な状態
                        elif _d['status'] == 'failed' or _d['status'] == 'limitExceeded' \
                                or _d['status'] == 'expired':
                            completed = False
                            LOGGER.error("Image export could be initialized but failed. device_id:{}, status:{}, export_id:{}".format(device_id, _d['status'], _d['exportId']))

            # exported_idに指定したダウンロード依頼の結果（可能、不可能）が判断できたら終了
            if _nc == num_of_images:
                if completed:
                    # 指定した数だけcompleteしたら終了。
                    LOGGER.debug("Exporting images finished successfully")
                else:
                    LOGGER.error("Exporting images finished. but failed. see above errors.")
                return _l

        # 指数バックオフ
        _sl = (2 ** backoff) + (random.randint(0, 1000) / 1000)
        LOGGER.debug(_sl)
        time.sleep(_sl) 
        backoff += 1
        if backoff > MAX_ATTEMPT:
            LOGGER.error("Exceed MAX_ATTEMPT")
            return None
        
        LOGGER.debug("Retrying {}".format(backoff))

    return None



'''
    開始終了時間と間隔を指定して、動画から静止画をダウンロードする。

        device_id : カメラのdevice id
        st_time : 開始時間(datetime型)
        ed_time : 終了時間(datetime型)
        interval : 静止画を抽出する間隔（sec）
        path: 静止画のダウンロード先
'''
def downloadImages(api_key, token, device_id, st_time, ed_time, interval, path):
#    LOGGER.debug(st_time)
#    LOGGER.debug(ed_time)
#    LOGGER.debug(interval)
    
    _st = SU.getUnixtime(st_time)
    _ed = SU.getUnixtime(ed_time)
    _it = int(interval*1000)

    # ダウンロード間隔の作成
    _trange = int(_ed - _st)
    if _trange > int(_it):
        _q = int(_trange / int(_it))
#        LOGGER.debug(_q)
        _rl = [ ( _st + x * int(_it)) for x in range(_q + 1)]
#        LOGGER.debug(_rl)
        _rl.append(_ed)
    else:
        _rl = [ _st, _ed ]
    LOGGER.debug('Exporting times at :')
    LOGGER.debug(_rl)

    _cnt = len(_rl)
    LOGGER.debug("Estimate Num. of Frames : {}".format(_cnt))

    # ダウンロード可能な静止画数の取得
    MAX_ATTEMPT = 5
    _js = getSoraCamExportUsage(api_key, token, device_id)
    if _js is not None:
        if "image" in _js:
            if "remainingFrames" in _js["image"]:
                LOGGER.debug("Remaining Num. of Frames : {}".format(_js["image"]["remainingFrames"]))
                if _cnt > int(_js["image"]["remainingFrames"]):
                    LOGGER.error("Remaining Frames Shortage. Stopped.")
                    return None
                else:
                    # 静止画のエクスポート開始
                    _n = 0
                    _fl = 0
                    _el = list()
                    for _i in _rl:
                        LOGGER.debug('\n')
                        LOGGER.debug('try exporting. time:{}, {}'.format(_i, SU.getDateTimeFromUnixTime(_i).strftime('%Y-%m-%d %H:%M:%S')))
                        # 静止画のエクスポート
                        _wk = getSoraCamExportImages(api_key, token, device_id, _i, True)
#                        LOGGER.debug(_wk)
                        # 静止画のエクスポート処理が済んだらexportIdをリストに溜め込んで、進捗にうつる。
                        # エラーの分は飛ばす。
                        if isinstance(_wk, dict):
                            if 'exportId' in _wk:
                                _el.append(_wk['exportId'])
                        else:
                            _fl += 1
                            LOGGER.error('Export failed. this might be because of 40x Error. device_id :{}, time : {}, {}'.format(device_id, _i, SU.getDateTimeFromUnixTime(_i).strftime('%Y%m%d %H%M%S')))
                                
                    LOGGER.debug("Exporting images initialized : {} frames. Failed {} frames".format(str(len(_el)), str(_fl)))

                    if len(_el) > 0:
                        # 静止画エクスポートの進捗　指数バックオフでMax_ATTEMPTまでトライする。
                        _l = waitSoraCamExportImages(api_key, token, device_id, _el, MAX_ATTEMPT)
                        if isinstance(_l, list):
                            pass
                        else:
                            LOGGER.error("静止画のエクスポートの進捗処理（waitSoraCamExportImages）が正常に終了しませんでした。")
                            return None

                        # URLからデータをダウンロードする。
                        if len(_l) > 0:
                            for _d in _l:
                                if 'url' in _d:
                                    # ファイル名を整形してDL
                                    SU.downloadImage(_d['url'], path)
                        
                        return True

    return None


'''
    開始終了時間と間隔を指定して、イベント画像をダウンロードする。

        device_id : カメラのdevice id
        st_time : 開始時間(datetime型)
        ed_time : 終了時間(datetime型)
        interval : 何秒間隔で静止画をDLするか
        path: 静止画のダウンロード先
'''
def downloadEventImages(api_key, token, device_id, st_time, ed_time, interval, path):
    _st = SU.getUnixtime(st_time)
    _ed = SU.getUnixtime(ed_time)

    # イベントの抽出
    _cnt = 0
    _rv = listSoraCamEventsForDevice(api_key, token, device_id, _st, _ed)
#    LOGGER.debug(json.dumps(_rv))
    if isinstance(_rv, list):
        if len(_rv) > 0:
            for _ts in _rv:
                if 'eventInfo' in _ts:
                    if 'atomEventV1' in _ts['eventInfo']:
                        if _ts['eventInfo']['atomEventV1']['type'] == 'motion' and _ts['eventInfo']['atomEventV1']['recordingStatus'] == 'completed':
                            _stt = _ts['eventInfo']['atomEventV1']['startTime']
                            _ett = _ts['eventInfo']['atomEventV1']['endTime']
                            _cnt += 1
                            _st = SU.getDateTimeFromUnixTime(_stt)
                            _ed = SU.getDateTimeFromUnixTime(_ett)
                            LOGGER.debug('\n')
                            LOGGER.debug('Exporting images Started. No.{}'.format(_cnt))
                            LOGGER.debug('recorderd startTime : {} sec, {}'.format(_st, _stt))
                            LOGGER.debug('recorderd endTime : {} sec, {}'.format(_ed, _ett))
                            # ダウンロード間隔の調整
                            _tl = (float(_ett) - float(_stt))/1000 # sec
                            LOGGER.debug('recorderd time : {} sec'.format(_tl))
                            LOGGER.debug('interval time : {} sec'.format(interval))
                            downloadImages(api_key, token, device_id, _st, _ed, interval, path)
        
    else:
        LOGGER.warning('イベントが抽出されませんでした。device: {}, {}-{}'.format(device_id, st_time.strftime('%Y%m%d %H%M%S'), ed_time.strftime('%Y%m%d %H%M%S')))
        return None
    
    return True



'''
	main

'''
if __name__ == "__main__":
    LOGGER.info('script start')
    start_time = time.time()

    parser = argparse.ArgumentParser(
            description='Create Time Lasp Video from Soracom Cam Recorded Video')
    parser.add_argument('--device', default='',
                        help='device id')
    parser.add_argument('--dir', default='tmp',
                        help='作業ディレクトリ')
    parser.add_argument('--start', default="", 
                        help='ダウンロード開始時間')
    parser.add_argument('--end', default="",
                    help='ダウンロード終了時間')
    parser.add_argument('--interval', default=60.0, type=float,
                    help='何秒間隔で静止画を抽出するか')

    args = parser.parse_args()

    ### パラメータのチェック
    #  デバイスidが引数として渡されているか
    if len(args.device) == 0:
        LOGGER.error("No deviceid")
        sys.exit()

    _now = datetime.now(TOKYO)
    # 開始時間と終了時間のフォーマットチェックとdatetime型への変換
    if len(args.start) > 0 and len(args.end):
#        LOGGER.debug(args.start)
#        LOGGER.debug(args.end)
        st_time = SU.convertFormattedStringDateTime(args.start)
        ed_time = SU.convertFormattedStringDateTime(args.end)
        if isinstance(st_time, datetime):
            pass
            if isinstance(ed_time, datetime):
                pass
            else:
                LOGGER.error("end_time {}".format(args.end))
                sys.exit()
        else:
            LOGGER.error("start_time {}".format(args.start))
            sys.exit()

        # 開始時間と終了時間の相関チェック。
        if SU.checkStartEndDatetime(st_time, ed_time, _now):
            pass
        else:
            LOGGER.error("Start > End")            
            sys.exit()
    else:
        ed_time = _now
        _wk = ed_time.strftime('%Y%m%d %H') + '0000'
        ed_time = datetime.strptime(_wk, '%Y%m%d %H%M%S')
        st_time = ed_time + timedelta(hours=-1)
    
    st_time_str = st_time.strftime('%Y%m%d%H%M%S')
    ed_time_str = ed_time.strftime('%Y%m%d%H%M%S')

    LOGGER.info('Requested Start Time : {}, {}'.format(st_time_str, SU.getUnixtime(datetime.strptime(st_time_str, '%Y%m%d%H%M%S'))))
    LOGGER.info('Requested End Time : {}, {}'.format(ed_time_str, SU.getUnixtime(datetime.strptime(ed_time_str, '%Y%m%d%H%M%S'))))
    
    interval = args.interval # sec

    # 作業ディレクトリ
    dpath = os.path.join(os.getcwd(), args.dir)

    # accessトークンの取得
    url = 'https://api.soracom.io/v1/auth'
    akey, token, oid, unm = SA.getToken(url, SORACOM_AUTH_KEY_ID, SORACOM_AUTH_KEY)
#    if not token == None:
#        LOGGER.debug(akey)
#        LOGGER.debug(oid)
#        LOGGER.debug(unm)
#        LOGGER.debug(token)
#    else:
#        LOGGER.debug("no token")

    if not token == None:
        # 静止画を作業ディレクトリにダウンロードする
        SU.clearDir(dpath)
        _rd = downloadEventImages(akey, token, args.device, st_time, ed_time, interval, dpath)

        if _rd:
            pass
        else:
            LOGGER.warning('{}のイベント画像のダウンロードが０件でした。'.format(args.device))
        
        # apiキーとトークンの無効化
        SA.revokeToken(akey, token)
        LOGGER.debug("token was revoked.")

    elapsed_time = time.time() - start_time
    LOGGER.info('script end')
    LOGGER.info('elapsed time : {} [sec]'.format(str(elapsed_time)))
