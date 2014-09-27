#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import re
import subprocess
import urllib.parse


pages = re.compile(r'(q=http.*?://.*?sverigesradio\.se/sida/avsnitt).+?(programid.+?)&')
pods = re.compile(r'(/topsy/ljudfil/.+?-mp3)')


def _google_program(s):
	param = urllib.parse.urlencode({'q': 'site:sverigesradio.se /sida/avsnitt %s' % s})
	html = subprocess.check_output('curl -H "user-agent: Mozilla/5.0" https://www.google.com/search?%s' % param, stderr=subprocess.DEVNULL).decode()
	try: link = next(pages.finditer(html))
	except: return []
	link = link.group(1)+'?'+link.group(2)
	link = urllib.parse.parse_qs(link)['q'][0].strip()
	html = subprocess.check_output('curl %s' % link, stderr=subprocess.DEVNULL).decode()
	return ['http://sverigesradio.se'+pod.group(1) for pod in pods.finditer(html)]

def search(s):
	urls = _google_program(s)
	return [ABSong(s, 'SR', u) for u in urls]
