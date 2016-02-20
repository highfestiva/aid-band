#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from killable import KillableThread
import re
from select import select
from time import sleep
from timeout import Timeout


keythread = None
keys = ''
keytimeout = Timeout()
keysleep = Timeout()
oldtcs = None


try:
	from msvcrt import getch
except:
	getch = None
if not getch:
	import sys,tty,termios
	try:
		oldtcs = termios.tcgetattr(sys.stdin)
		tty.setraw(sys.stdin.fileno())
	except:
		def getch():
			s = ''
			while not s:
				s = sys.stdin.read(1)
				if not s:
					sleep(0.1)
			return s,ord(s)
if not getch:	
	emuchars = ''
	def getch():
		global emuchars
		if emuchars:
			ch,emuchars = emuchars[0],emuchars[1:]
			return ch
		def ir():
			s = sys.stdin.read(1)
			#print(s,ord(s),end='\r\n')
			return s,ord(s)
		s,o = ir()
		if o == 27:
			s,o = ir()
			if o == 27:
				return s
			if o == 79:	# xterm F1-F5
				emuchars += chr(ir()[1]-21)
				return chr(0)
			elif o == 91:
				s,o = ir()
				if o == 65: emuchars += chr(72); return chr(0xE0)
				if o == 66: emuchars += chr(80); return chr(0xE0)
				if o == 67: emuchars += chr(77); return chr(0xE0)
				if o == 68: emuchars += chr(75); return chr(0xE0)
				if o == 70: emuchars += chr(79); return chr(0xE0)	# xterm end
				if o == 52: emuchars += chr(79); ir(); return chr(0xE0)	# console end
				if o == 91:	# console F1-F5
					emuchars += chr(ir()[1]-6)
					return chr(0)
				o = o*100 + ir()[1]
				ir()
				if o == 4953: emuchars += chr(63); return chr(0)
				if o == 4955: emuchars += chr(64); return chr(0)
				if o == 4956: emuchars += chr(65); return chr(0)
				if o == 4957: emuchars += chr(66); return chr(0)
				if o == 5048: emuchars += chr(67); return chr(0)
				if o == 5049: emuchars += chr(68); return chr(0)
				if o == 5051: emuchars += chr(133);
				if o == 5052: emuchars += chr(134);
				return chr(0xE0)
		print(s, end='', flush=True)
		return s

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
			ch,keys = '<quit>',''
		ch = ch if type(ch) == str else ch.decode('cp850')
		if ch == '\b':
			keys = keys[:len(keys)-1] if keys else ''
		else:
			keys += ch
		if handle_keys:
			handle_keys(keys)
		keytimeout.reset()

def stop():
	if oldtcs:
		import termios
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtcs)
	try:	keythread.stop()
	except:	pass

def init(handle_keys=None):
	global keythread
	keythread = KillableThread(target=readkeys, args=[handle_keys])
	keythread.start()

if __name__ == '__main__':
	def p(x):
		print('out:', x, [ord(y) for y in x], end='\r\n',flush=True)
		if '<quit>' in x:
			stop()
			import sys
			sys.exit(0)
	readkeys(p)
