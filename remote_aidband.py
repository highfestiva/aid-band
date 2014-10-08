#!/usr/bin/env python

from msvcrt import kbhit,getch
import socket
import sys


host = sys.argv[1] if len(sys.argv) >= 2 else 'localhost'
port = 3303
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
	s.connect((host,port))
	s.settimeout(1)
	sendqueue = sys.argv[2:]
	bb = b''
	while True:
		try:
			bb += s.recv(1)
			sys.stdout.write(bb.decode())
			sys.stdout.flush()
			bb = b''
		except socket.timeout:
			if sendqueue:
				d = eval('"'+sendqueue[0]+'"')
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
