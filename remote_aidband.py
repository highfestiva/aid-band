#!/usr/bin/env python

import argparse
from msvcrt import kbhit,getch
import socket
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-t','--host', dest='host', default='localhost:3303', help="host (and optional port) to connect to, defaults to localhost:3303")
parser.add_argument('-p','--use-password-file', dest='usepw', default=False, action='store_true', help="use file 'password' (containing password without linefeeds) instead of manual entry")
parser.add_argument('-c','--command', dest='commands', action='append', default=[], help="pass command(s) to be sent initially")
options = parser.parse_args()

host,port = options.host.split(':') if ':' in options.host else (options.host,3303)
port = int(port)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
	s.connect((host,port))
	s.settimeout(1)
	pw = [open('password').read()+'\\r'] if options.usepw else []
	sendqueue = pw + options.commands
	bb = b''
	while True:
		try:
			bb += s.recv(1)
			sys.stdout.write(bb.decode())
			sys.stdout.flush()
			bb = b''
		except socket.timeout:
			if sendqueue:
				d = eval("'''"+sendqueue[0]+"'''")
				s.send(d.encode())
				sendqueue = sendqueue[1:]
				continue
		except UnicodeDecodeError as e:
			pass
		while kbhit():
			ch = getch()
			if ord(ch) == 0:
				ch = getch()
				if ord(ch) >= 59 and ord(ch) <= 68:
					ch = ('<F%i>' % (ord(ch)-58)).encode()
				else:
					continue
			elif ord(ch) == 0xE0:
				ch = getch()
				if   ord(ch) ==  75: ch = '<Left>'.encode()
				elif ord(ch) ==  77: ch = '<Right>'.encode()
				elif ord(ch) ==  72: ch = '<Up>'.encode()
				elif ord(ch) ==  80: ch = '<Down>'.encode()
				elif ord(ch) == 133: ch = '<F11>'.encode()
				elif ord(ch) == 134: ch = '<F12>'.encode()
			s.send(ch.decode('cp850').encode())
	s.close()
except socket.error as e:
	value,message = e.args[:2]
	try: s.close()
	except: pass
	print("Socket closed: " + message)
