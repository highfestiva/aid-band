#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from killable import KillableThread
from msvcrt import getch
import re
from time import sleep
from timeout import Timeout

keythread = None
keys = ''
keytimeout = Timeout()
keysleep = Timeout()

def peekstr(timeout=10):
	if keytimeout.timeout(timeout):
		keytimeout.reset()
		global keys
		keys = ''
	elif re.match('^[^\t<>+-]+\r$', keys):
		return getstr()
	elif re.match('^[^\t<>+-]+$', keys):
		# Not finished typing yet.
		return ''
	# Possibly hotkey or such.
	return getstr()

def getstr():
	global keys
	ks,keys = keys,''
	return ks

def readkeys(handle_keys):
	keytimeout.reset()
	global keys
	while True:
		ch = getch()
		if ord(ch) == 0:
			ch = getch()
			if ord(ch) >= 59 and ord(ch) <= 68:
				ch = '<F%i>' % (ord(ch)-58)
			else:
				continue
		elif ord(ch) == 0xE0:
			ch = getch()
			if   ord(ch) ==  75: ch = '<Left>'
			elif ord(ch) ==  77: ch = '<Right>'
			elif ord(ch) ==  72: ch = '<Up>'
			elif ord(ch) ==  80: ch = '<Down>'
			elif ord(ch) == 133: ch = '<F11>'
			elif ord(ch) == 134: ch = '<F12>'
			elif ord(ch) ==  79: ch = '<End>'
			else: continue
		elif ord(ch) == 3:
			keys = '<quit>'
			keytimeout.reset()
			continue
		ch = ch if type(ch) == str else ch.decode('cp850')
		if ch == '\b':
			keys = keys[:len(keys)-1] if keys else ''
		else:
			keys += ch
		handle_keys(keys)
		keytimeout.reset()

def stop():
	keythread.stop()

def init(handle_keys):
	global keythread
	keythread = KillableThread(target=readkeys, args=[handle_keys])
	keythread.start()
