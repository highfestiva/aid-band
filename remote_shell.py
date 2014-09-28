#!/usr/bin/env python

from msvcrt import kbhit,getch
import socket
import sys


host = sys.argv[1]
port = 3303
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
	print("Connecting...")
	s.connect((host,port))
	s.settimeout(1)
	while True:
		try:
			sys.stdout.write(s.recv(1).decode())
			sys.stdout.flush()
		except socket.timeout:
			pass
		while kbhit():
			ch = getch()
			print(ord(ch))
			if ord(ch) == 0:
				ch = getch()
				print(ord(ch))
				if ord(ch) >= 59 and ord(ch) <= 68:
					ch = ('<F%i>' % (ord(ch)-58)).encode()
				else:
					continue
			elif ord(ch) == 0xE0:
				ch = getch()
				print(ord(ch))
				if   ord(ch) ==  72: ch = '<Up>'.encode()
				elif ord(ch) ==  80: ch = '<Down>'.encode()
				elif ord(ch) == 133: ch = '<F11>'.encode()
				elif ord(ch) == 134: ch = '<F12>'.encode()
			s.send(ch)
	s.close()
except socket.error as e:
	value,message = e.args[:2]
	try: s.close()
	except: pass
	print("Could not open socket: " + message)
