#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from killable import KillableThread
import re
import socket
from time import sleep
from timeout import Timeout
from threading import Thread


acpt = None
acpt_sock = None
input = ''
clients = []
keytimeout = Timeout()


def peekstr(timeout=10):
	if keytimeout.timeout(timeout):
		keytimeout.reset()
		global input
		input = ''
	elif re.match('^[^\t<>+-]+\r$', input):
		return getstr()
	elif re.match('^[^\t<>+-]+$', input):
		# Not finished typing yet.
		return ''
	# Possibly hotkey or such.
	return getstr()

def getstr():
	global input
	i,input = input,''
	return i

def handlecmd(client, handle_login, handle_keys):
	global input
	bb = b''
	try:
		print('Remote network shell authenticated and running.')
		handle_login()
		while True:
			sleep(0.001)
			bb += client.recv(1)
			if not bb:
				sleep(0.1)
				raise 'Disconnected?'
			try:
				i = bb.decode()
				bb = b''
			except Exception as e:
				print(e)
				continue
			if i == '\b':
				input = input[:-1]
			else:
				input += i
			handle_keys(input)
			keytimeout.reset()
	except Exception as e:
		print('Remote network shell connection dropped.')
		dropclient(client)

def dropclient(client):
	global clients
	try:
		clients.remove(client)
	except Exception as e:
		print(e)
	try:
		client.close()
	except Exception as e:
		print(e)

def listen(handle_login, handle_keys):
	global clients, acpt_sock
	acpt_sock = s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('',3303))
	s.listen(2)
	while 1:
		sleep(0.1)
		client,address = s.accept()
		print('New remote network shell connected.')
		try:
			client.send('Password: '.encode())
			pw,i = '',0
			while '\r' not in pw and len(pw)<50 and i<50:
				sleep(0.01)
				pw += client.recv(1).decode()
				i += 1
			client.send('\n'.encode())
			wanted_password = open('password').read() + '\r'
			if pw != wanted_password:
				print('Bad password entered by client.')
				dropclient(client)
				continue
			clients += [client]
			Thread(target=handlecmd, args=[client,handle_login,handle_keys]).start()
		except Exception as e:
			print(e)
			dropclient(client)
			print('Remote network shell dropped during password entry.')


def output(s):
	d = (s+'\r\n').encode()
	for c in clients:
		try:
			c.send(d)
		except Exception as e:
			print(e)

def stop():
	try: acpt_sock.close()
	except: pass
	try: [c.close() for c in clients]
	except: pass
	clients = []
	acpt.stop()
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('localhost',3303))
		s.close()
	except:
		pass

def init(handle_login, handle_keys):
	global acpt
	acpt = KillableThread(target=listen, args=[handle_login, handle_keys])
	acpt.start()
