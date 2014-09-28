from msvcrt import getch
import re
import sys
from time import time
from threading import Thread

keys = ''
hittime = None

def _timeout(t):
	global hittime
	if hittime and time()-hittime > t:
		hittime = time()
		return True
	return False

def peekstr(timeout=10):
	if _timeout(timeout):
		global keys
		keys = ''
	elif re.match('^[^<>+-]+\r$', keys):
		return getstr()
	elif re.match('^[^<>+-]+$', keys):
		# Not finished typing yet.
		return ''
	# Possibly hotkey or such.
	return getstr()

def getstr():
	global keys
	ks = keys
	keys = ''
	return ks

def main():
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
			if   ord(ch) ==  72: ch = '<Up>'
			elif ord(ch) ==  80: ch = '<Down>'
			elif ord(ch) == 133: ch = '<F11>'
			elif ord(ch) == 134: ch = '<F12>'
			else: continue
		elif ord(ch) == 3:
			keys = '<quit>'
			hittime = time()
			sys.exit(0)
			break
		ch = ch if type(ch) == str else ch.decode('cp850')
		if ch == '\b':
			keys = keys[:len(keys)-1] if keys else ''
		else:
			keys += ch
	hittime = time()

Thread(target=main).start()
