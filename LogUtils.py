'''
    Loggerの切り替えを簡単にするためのユーティリティ

'''
import os, re, sys
from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG, INFO

'''
    Screen出力のロガー
'''
def setScreenLogger(LOGGER, LOG_FMT, level):
    formatter = Formatter(LOG_FMT)

    LOGGER.setLevel(DEBUG)
    if level == 'info':
        LOGGER.setLevel(INFO)

    if level != 'debug' and level != 'info':
        LOGGER.error('in setLogger : LEVEL must be debug/info. set to debug.')

    sh = StreamHandler()
    sh.setFormatter(formatter)
    LOGGER.addHandler(sh)

    return LOGGER

'''
    File出力のロガー
'''
def setFileLogger(LOGGER, LOG_FMT, level, filepath, screen=False):
    formatter = Formatter(LOG_FMT)

    LOGGER.setLevel(DEBUG)
    if level == 'info':
        LOGGER.setLevel(INFO)

    if level != 'debug' and level != 'info':
        LOGGER.error('in setLogger : LEVEL must be debug/info. set to debug.')

    if len(filepath) == 0:
        sh = StreamHandler()
        sh.setFormatter(formatter)
        LOGGER.addHandler(sh)
        LOGGER.error('in setLogger : FILEPATH must be set when file handler is selected. set to stream.')
    else:
        fh = FileHandler(filepath)
        fh.setFormatter(formatter)
        LOGGER.addHandler(fh)
        if screen:
            sh = StreamHandler()
            sh.setFormatter(formatter)
            LOGGER.addHandler(sh)


    return LOGGER


'''
	main

'''
if __name__ == "__main__":
    # logging
    LOGGER = getLogger(os.path.basename(__file__))
    LOG_FMT = "[%(name)s] %(asctime)s %(levelname)s %(lineno)s %(message)s"
#    formatter = Formatter(LOG_FMT)

    if not setFileLogger(LOGGER, LOG_FMT, 'info', 'log.log'):
        sys.exit()


    LOGGER.info('script start')
    LOGGER.debug('debug')
    LOGGER.info('script end')
