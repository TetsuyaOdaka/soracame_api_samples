import os, re

from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG, INFO
from datetime import datetime, timedelta
import time
import shutil
import urllib

import LogUtils as LU
import soracom_auth as SA

SCRIPT_NAME = os.path.basename(__file__)
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__)) # スクリプトのあるディレクトリの絶対パス

# logging
LOGGER = getLogger(os.path.basename(__file__))
LOG_FMT = "[%(name)s] %(asctime)s %(levelname)s %(lineno)s %(message)s"

LOGGER = LU.setScreenLogger(LOGGER, LOG_FMT, 'debug') # develop

'''
    Unixtimeを取得するためのユーティリティー
    dt : datetime型
    delta : 分

'''
def getUnixtime(dt, delta=0):

#    LOGGER.debug(int(dt.timestamp()*1000))
    _d = dt + timedelta(minutes=delta)
    _rt = int(_d.timestamp()*1000)

    return _rt

'''
    ミリ秒単位のUnixtimeからdatetimeを取得する
    ut : int型 unixtime（13桁）

'''
def getDateTimeFromUnixTime(ut):

    _rt = datetime.fromtimestamp(ut/1000)

    return _rt

'''
    urlを指定して静止画をダウンロードする。
    https://note.nkmk.me/python-download-web-images/

    seq : ダウンロードしたイメージにsequence numberを振りたい時指定（イベント画像のダウンロード時）

'''
def downloadImage(url, path, seq=''):

    # ファイル名
    _fn = url.split('?')[0] # パラメータを削除
    _fn = _fn.split('/')[-1] # urlからファイル名&パラメータを取得
    if len(seq) > 0:
        _fn = str(seq) + '_' + _fn
    _fp = path + '/' + _fn
    with urllib.request.urlopen(url) as web_file:
        with open(_fp, 'wb') as local_file:
            local_file.write(web_file.read())

    LOGGER.debug('write {}'.format(_fn))

    return _fp



'''
    ディレクトリを空にする
'''
def clearDir(path):

    if os.path.exists(path):
        shutil.rmtree(path)

    os.mkdir(path)
    
    return None

'''
    文字列の日時のフォーマットをチェックして、DateTime型を戻す
    フォーマット："%Y%m%d %H%M%S"の文字列

'''
def convertFormattedStringDateTime(dt):
    # Timezoneを明示的に指定するため、awareなdatetimeにparseしたい。
    dt += ' +0900'
    s_format = '%Y%m%d %H%M%S %z'
    LOGGER.debug("convert {}".format(dt))

    # フォーマットのチェック
    if ' ' in dt:
        _ar = dt.split(' ')
        if len(_ar[0]) == 8 and len(_ar[1]) == 6:
            # %Y%m%d 20120112
            _m = re.match(r'20[0-9][0-9][01][0-9][0-3][0-9]', _ar[0])
            if _m is not None:
                # %H%M%S 081030
                _n = re.match(r'[0-2][0-9][0-6][0-9][0-6][0-9]', _ar[1])
                if _n is not None:
                    # OK
                    _rt = datetime.strptime(dt, s_format)
                    LOGGER.debug('datetime conv OK.')
                    return _rt
                else:
                    LOGGER.error('datetime conv error. format %H%M%S')
                    return False
            else:
                LOGGER.error('datetime conv error. format %Y%m%d')
                return False
        else:
            LOGGER.error('datetime conv error. format %Y%m%d %H%M%S')
            return False

    return False


'''
    開始日時（datetime型）と終了日時（datetime型）の相関チェック

'''
def checkStartEndDatetime(st, ed, nw=None):
    # 引数はともにdatetime型
    if isinstance(st, datetime):
        pass
        if isinstance(ed, datetime):
            pass
        else:
            LOGGER.error("end_time {}".format(ed))
            return False
    else:
        LOGGER.error("start_time {}".format(st))
        return False

    # 開始時間は終了時間より前
    if st >= ed:
        LOGGER.error("start_time >= end_time : start _time {}, end_time {}".format(st, ed))
        return False
    
    if nw is not None:
        # 開始時間も終了時間も今より前
        if ed >= nw:
            LOGGER.error("arg  end_time >= now : end_time {}".format(ed))
            return False

    return True


'''
	main

'''
if __name__ == "__main__":
    LOGGER.info('script start')
    start_time = time.time()

    # 現在時刻をUnixtime（13桁）にする
    _w = getUnixtime(datetime.now(), 0)
    LOGGER.debug('Now   {}'.format(_w))
    # 13桁のUnixtimeからDatetimeにする
    _w = getDateTimeFromUnixTime(_w)
    LOGGER.debug('Now   {}'.format(_w))

    # 10分後の時刻をUnixtime（13桁）にする
    _w = getUnixtime(datetime.now(), 10)
    LOGGER.debug('10min {}'.format(_w))
    # 10桁のUnixtimeからDatetimeにする
    _w = getDateTimeFromUnixTime(_w)
    LOGGER.debug('10min {}'.format(_w))


    elapsed_time = time.time() - start_time
    LOGGER.info('script end')
    LOGGER.info('elapsed time : {} [sec]'.format(str(elapsed_time)))
