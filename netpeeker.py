#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from killable import KillableThread
import re
import socket
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

def handlecmd(client, handle_keys):
	global input
	bb = b''
	try:
		print('Remote network shell authenticated and running.')
		client.send('\nWelcome to AidBand command interface!\n'.encode())
		while True:
			bb += client.recv(1)
			try:
				i = bb.decode()
				bb = b''
			except:
				continue
			if i == '\b':
				input = input[:len(input)-1] if input else ''
			else:
				input += i
			handle_keys(input)
			keytimeout.reset()
	except Exception as e:
		dropclient(client)
		print('Remote network shell connection dropped.')

def dropclient(client):
	global clients
	try:
		clients.remote(client)
		client.close()
	except:
		pass

def listen(handle_keys):
	global clients, acpt_sock
	acpt_sock = s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('',3303))
	s.listen(2)
	while 1:
		client,address = s.accept()
		clients += [client]
		print('New remote network shell connected.')
		try:
			client.send('Password: '.encode())
			pw,i = '',0
			while '\r' not in pw and len(pw)<50 and i<50:
				pw += client.recv(1).decode()
				i += 1
			wanted_password = open('password').read() + '\r'
			if pw != wanted_password:
				print('Bad password entered by client.')
				dropclient(client)
				continue
			Thread(target=handlecmd, args=[client,handle_keys]).start()
		except Exception as e:
			dropclient(client)
			print(e)
			print('Remote network shell dropped during password entry.')


def output(s):
	d = (s+'\r\n').encode()
	for c in clients:
		try: c.send(d)
		except: pass

def stop():
	try: acpt_sock.close()
	except: pass
	try: [c.close() for c in clients]
	except: pass
	acpt.stop()
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('localhost',3303))
		s.close()
	except:
		pass

def init(handle_keys):
	global acpt
	acpt = KillableThread(target=listen, args=[handle_keys])
	acpt.start()
