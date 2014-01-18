#!/usr/bin/env python
#-*-coding: utf-8 -*-
import cookielib
import logging
import sys
import urllib2
from piao.config import DATA_DIR

reload(sys)
sys.setdefaultencoding('utf-8')

headers = [
    ('Accept', '*/*'),
    ('Accept-Encoding', 'deflate'),
    ('Accept-Language', 'en-US,zh-CN;q=0.8,zh-TW;q=0.6'),
    ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36'),
    ('Connection', 'Keep-Alive'),
]

cookie = cookielib.LWPCookieJar(DATA_DIR + '/cookie.dat')
try:
    cookie.load(ignore_discard=True, ignore_expires=True)
except IOError:
    pass
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
opener.addheaders = headers
urllib2.install_opener(opener)

logger = logging.getLogger('piao')
_formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s %(message)s')
_sh = logging.StreamHandler()
_fh = logging.FileHandler(DATA_DIR + '/piao.log')
_sh.setFormatter(_formatter)
_fh.setFormatter(_formatter)
logger.addHandler(_sh)
logger.addHandler(_fh)
logger.setLevel(logging.DEBUG)
