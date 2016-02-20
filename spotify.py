#!/usr/bin/env python3

import sock
import socket
import spotipy
import subprocess
from sys import platform


cmd = 'Consoleify.exe' if platform=='win32' else './Consoleify' 
sp = spotipy.Spotify()
sp.max_get_retries = 1


class Client:
	def __init__(self, username, password):
		self._cmd = [cmd, username, password]
		self._proc = None
		try:
			self._reset()
		except:
			self.quit()
			raise

	def popular(self):
		s = self._run('toplist')
		return self._parsesongs(s)

	def search(self, song):
		#s = self._run('search-song %s'%song)
		#return self._parsesongs(s)
		found = sp.search(song)
		if not found:
			return []
		tracks = found['tracks']['items']
		# print()
		# import pprint
		# pprint.pprint(tracks)
		songs = [Song(t['name'], t['popularity'], t['artists'][0]['name'], t['artists'], t['uri']) for t in tracks]
		return sorted(songs, key=lambda s: s.popularity, reverse=True)

	def playsong(self, uri):
		s = self._run('play-song %s'%uri)
		return 'Playing ' in s

	def isplaying(self):
		s = self._run('is-playing')
		return s == 'yes\n'

	def stop(self):
		s = self._run('stop')
		return 'Stopped.'

	def quit(self):
		self._io('quit\n', timeout=0.5)
		self._proc.kill()
		self._proc.wait()

	def _parsesongs(self, s):
		songs = []
		for song in s.split('\n'):
			info = song.strip()
			if info.startswith('song '):
				info = info[5:]
				comps = info.split('~~~')
				if len(comps) == 4:
					name,popularity,artists,uri = [c.strip() for c in comps]
					artists = artists.split('~')
					songs += [Song(name,int(popularity),artists[0],artists,uri)]
		return songs

	def _run(self, c):
		self._io()
		try:
			o = self._io('%s\n'%c, timeout=5)
		except socket.error:
			o = 'error'
		if 'error' in o.lower():
			self._reset()
			return ''
		return o

	def _reset(self):
		self._sock = sock.socket()
		if self._proc:
			try:
				self._proc.kill()
				self._proc.wait()
			except:
				pass
		self._proc = subprocess.Popen(self._cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		if not self._sock.connect(('localhost',55552)):
			raise SystemError('Consoleify not responding.')
		try:
			o = self._io(timeout=15)
		except socket.error:
			self.quit()
			o = None
		if not o:
			raise SystemError('Unable to login to Spotify due to timeout!')
		if 'Login ok.' not in o:
			self.quit()
			raise NameError('Spotify login failed (user/pass incorrect?)!')

	def _io(self, input=None, timeout=0.0001):
		if input:
			self._sock.send(input)
		self._sock.settimeout(timeout)
		return self._sock.recvchunk()


class Song:
	def __init__(self, name, popularity, artist, artists, uri):
		self.name,self.popularity,self.artist,self.artists,self.uri = name,popularity,artist,artists,uri


if __name__ == '__main__':
	print('logging in and playing summat')
	c = Client('your username', 'your password')
	s = c.popular()[-1]
	c.playsong(s.uri)
	from time import sleep
	sleep(5)
	print('changing song')
	s = c.search('Chandelier')[0]
	c.playsong(s.uri)
	sleep(5)
	c.quit()
	print('done')
