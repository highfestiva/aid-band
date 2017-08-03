#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
from collections import OrderedDict
import re
import subprocess
import urllib.parse


pages = re.compile(r'(q=http.*?://[a-z\.-_]*?sverigesradio\.se/sida/avsnitt).+?(programid.+?)&')
pods = re.compile(r'(/topsy/ljudfil/.+?\.mp3)')


def _google_program(s):
    param = urllib.parse.urlencode({'q': 'site:sverigesradio.se /sida/avsnitt %s' % s})
    url = 'https://www.google.se/search?%s' % param
    html = subprocess.check_output('curl -H "user-agent: Mozilla/5.0" %s' % url, stderr=subprocess.DEVNULL).decode()
    try: link = next(pages.finditer(html))
    except: return []
    link = link.group(1)+'?'+link.group(2)
    link = urllib.parse.parse_qs(link)['q'][0].strip()
    html = subprocess.check_output('curl %s' % link, stderr=subprocess.DEVNULL).decode()
    return ['http://sverigesradio.se'+pod.group(1) for pod in pods.finditer(html)]

def search(s):
    urls = _google_program(s)
    urls = OrderedDict((url,url) for url in urls).values() # uniqify
    return [ABSong(s, 'SR', u) for u in urls]


# songs = search('sommar')
# print([s.uri for s in songs])
