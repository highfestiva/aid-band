#!/usr/bin/env python3

import argparse
import keypeeker
import socket
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-t','--host', dest='host', default='localhost:3303', help="host (and optional port) to connect to, defaults to localhost:3303")
parser.add_argument('-p','--use-password-file', dest='usepw', default=False, action='store_true', help="use file 'password' (containing password without linefeeds) instead of manual entry")
parser.add_argument('-c','--command', dest='commands', action='append', default=[], help="pass command(s) to be sent initially")
options = parser.parse_args()

keypeeker.init()

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
		s = keypeeker.peekstr(0.1)
		if s:
			s.send(s.decode('cp850').encode() if 'win' in sys.platform.lower() else s)
	s.close()
except socket.error as e:
	value,message = e.args[:2]
	try: s.close()
	except: pass
	print("Socket closed: " + message)

keypeeker.stop()
