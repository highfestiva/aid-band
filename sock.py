#!/usr/bin/env python3

from select import select
import socket as _socket
from time import time,sleep

class socket:
	def __init__(self):
		self.s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
		self.s.setblocking(0)
		self.timeout = 0.1

	def connect(self, hostport):
		self.hostport = (_socket.gethostbyname(hostport[0]), hostport[1])
		for x in range(15*10):
			try:
				self.send('ping\n')
				if self.recv(5) == 'pong\n':
					return True
			except _socket.error:
				sleep(0.1)
		return False

	def close(self):
		try:
			self.send('quit\n'.encode())
			self.s.shutdown(_socket.SHUT_RDWR)
			time.sleep(0.01)
		except:
			pass
		return self.s.close()

	def settimeout(self, t):
		self.timeout = t

	def send(self, data):
		data = data.encode()
		if self.s.sendto(data, self.hostport) != len(data):
			raise _socket.error('unable to send')

	def recv(self, l):
		if self.timeout != None:
			r,_,e = select([self.s],[],[self.s], self.timeout)
			if e: raise _socket.error('disconnected')
			if not r: raise _socket.error('timeout')
		data,hostport = self.s.recvfrom(l)
		if hostport == self.hostport:
			return data.decode()

	def recvchunk(self):
		s = ''
		t0,to = time(),self.timeout
		while time()-t0 <= to:
			try:
				s += self.recv(1024)
			except _socket.error:
				break
			self.timeout = 0.1
		self.timeout = to
		return s
