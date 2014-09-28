import re
import socket
import sys
from time import time
from threading import Thread


acpt = None
input = ''
hittime = None


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

def handlecmd(client):
	global input
	try:
		client.send('\nWelcome to AidBand command interface!\n'.encode())
		while True:
			i = client.recv(1).decode()
			input += i
			if '\r' in i: i += '\n'
			client.send(i.encode())
	except Exception as e:
		print(e)
		print('Connection dropped.')
		try: client.close()
		except: pass

def listen():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('',3303))
	s.listen(2)
	while 1:
		client,address = s.accept()
		try:
			client.send('Password: '.encode())
			pw,i = '',0
			while '\r' not in pw and len(pw)<50 and i<50:
				pw += client.recv(1).decode()
				i += 1
				print(pw)
			if pw != '+-*/~\r':
				print('Bad password %s.' % pw)
				client.close()
				continue
			Thread(target=handlecmd, args=[client]).start()
		except Exception as e:
			print(e)
			print('Connection dropped.')

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

acpt = KillableThread(target=listen)
acpt.start()
