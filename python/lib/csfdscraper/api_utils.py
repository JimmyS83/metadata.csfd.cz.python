# coding: utf-8

from __future__ import absolute_import, unicode_literals

import json, xbmc
#from pprint import pformat
try: #PY2 / PY3
    from urllib2 import Request, urlopen
    from urllib2 import URLError
    from urllib import urlencode
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    from urllib.parse import urlencode
try:
    from typing import Text, Optional, Union, List, Dict, Any  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

HEADERS = {}


def set_headers(headers):
    HEADERS.update(headers)


def load_info(url, params=None, default=None, resp_type = 'json'):
    theerror = ''
    if params:
        url = url + '?' + urlencode(params)
    #xbmc.log('Calling URL "{}"'.format(url), xbmc.LOGDEBUG)
    req = Request(url, headers=HEADERS)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            theerror = {'error': 'failed to reach the remote site\nReason: {}'.format(e.reason)}
        elif hasattr(e, 'code'):
            theerror = {'error': 'remote site unable to fulfill the request\nError code: {}'.format(e.code)}
        if default is not None:
            return default
        else:
            return theerror
    if resp_type.lower() == 'json':
        resp = json.loads(response.read().decode('utf-8'))
    else:
        resp = response.read().decode('utf-8')
    
    #xbmc.log('the api response:\n{}'.format(pformat(resp)), xbmc.LOGDEBUG)
    return resp