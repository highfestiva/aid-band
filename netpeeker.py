import re
import socket
import sys
from time import time
from threading import Thread


acpt = None
input = ''
hittime = None
clients = []


def _timeout(t):
	global hittime
	if hittime and time()-hittime > t:
		hittime = time()
		return True
	return False

def peekstr(timeout=10):
	if _timeout(timeout):
		global input
		input = ''
	elif re.match('^[^<>+-]+\r$', input):
		return getstr()
	elif re.match('^[^<>+-]+$', input):
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
			if '\r' in i: i += '\n'
			client.send(i.encode())
	except Exception as e:
		print(e)
		print('Connection dropped.')
		dropclient(client)

def dropclient(client):
	global clients
	try:
		clients.remote(client)
		client.close()
	except:
		pass

def listen(handle_keys):
	global clients
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('',3303))
	s.listen(2)
	while 1:
		client,address = s.accept()
		clients += [client]
		try:
			client.send('Password: '.encode())
			pw,i = '',0
			while '\r' not in pw and len(pw)<50 and i<50:
				pw += client.recv(1).decode()
				i += 1
			if pw != '+-*/~\r':
				print('Bad password %s.' % pw)
				dropclient(client)
				continue
			Thread(target=handlecmd, args=[client,handle_keys]).start()
		except Exception as e:
			dropclient(client)
			print(e)
			print('Connection dropped during password entry.')


def output(s):
	d = (s+'\r\n').encode()
	for c in clients:
		try: c.send(d)
		except: pass

def stop():
	acpt.stop()
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('localhost',3303))
		s.close()
	except:
		pass

class KillableThread(Thread):
	def _bootstrap(self):
		self._killme = False
		sys.settrace(self._trace)
		super()._bootstrap()
	def stop(self):
		self._killme = True
	def _trace(self, frame, event, arg):
		if self._killme:
			sys.exit(0)
		return self._trace

def init(handle_keys):
	global acpt
	acpt = KillableThread(target=listen, args=[handle_keys])
	acpt.start()
