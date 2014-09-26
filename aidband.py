#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import difflib
from grooveshark import Client
import hotoptions
import keypeeker
import os.path
import re
import subprocess
import sys
import time
import traceback

proc = None
start_play_time = time.time()
caching_name = None
gs = None
listname = None
playlist = []
playqueue = []
playidx = 0

def stop():
	global proc,caching_name
	if proc:
		proc.kill()
		if caching_name:
			os.remove(caching_name)
			caching_name = None

def play_url(url, cachename):
	stop()
	global proc,start_play_time,caching_name
	caching_name = None
	cmd = ['mplayer.exe', url]
	if cachename and url.startswith('http'):
		cmd += ['-dumpstream', '-dumpfile', cachename]
		caching_name = cachename
	proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	start_play_time = time.time()

def play_idx():
	global playqueue,playidx
	if playidx < len(playqueue):
		song = playqueue[playidx]
		print(_pfixs(song.artist), '-', _pfixs(song.name))
		if song in playlist:
			fn = ('cache/'+song.artist+'-'+song.name+'.mpeg').lower().replace(' ','_')
			url = fn if os.path.exists(fn) else song.stream.url
		else:
			fn = None
			url = song.stream.url
		if not url:
			update_url()
			url = song.stream.url
		play_url(url, fn)

def poll():
	if not proc or proc.poll() == None:
		return
	if caching_name:
		play_idx()	# Play cache.
	elif time.time()-start_play_time < 5.0:	# Stopped after short amount of time? URL probably fucked.
		if update_url():
			play_idx()
		else:
			next_song()
	else:
		next_song()

def play_list(name):
	global listname
	listname = name
	global playlist,playqueue,playidx
	if listname == hotoptions.Hit:
		playqueue = list(gs.popular())
		listname = hotoptions.My
		playlist = load_list()
	else:
		playlist = playqueue = load_list()
	playidx = 0
	if playqueue:
		play_idx()
	else:
		stop()

def play_search(search):
	songs = []
	try:
		artists = sorted(gs.search(search, type=Client.ARTISTS), key=lambda a: _match_ratio(a.name, search), reverse=True)
		if artists:
			# Get extact match if possible.
			arts = [a for a in artists if a.name.lower() == search]
			artists = arts if arts else artists
			# Add most popular songs, and see which one we're after.
			arts = []
			for a in artists:
				score = 0
				i = 0
				for s in a.songs:
					score += int(s.popularity)
					i += 1
					if i >= 10:
						break
				arts += [(a,score)]
			artist = sorted(arts, key=lambda l:l[1], reverse=True)[0][0]
			# If searching for artist, pick all songs, sort by popularity and remove redundant.
			ss = sorted(artist.songs, key=lambda s: int(s.popularity), reverse=True)
			# Uniquify.
			names = set()
			for s in ss:
				if s.name not in names:
					names.add(s.name)
					songs.append(s)
	except StopIteration:
		try:
			# If searching for songs, just pick first hit.
			songs = [next(gs.search(search, type=Client.SONGS))]
		except StopIteration:
			pass
	queue_songs(songs)

def add_song():
	global playlist,playqueue,playidx
	if playqueue[playidx:playidx+1]:
		playlist += playqueue[playidx:playidx+1]
		save_list(playlist)

def drop_song():
	global playlist,playqueue,playidx
	if playidx < len(playqueue):
		song = playqueue[playidx]
		playqueue = playqueue[:playidx] + playqueue[playidx+1:]
		playlist = list(filter(lambda s: s!=song, playlist))
		play_idx()

def prev_song():
	global playlist,playqueue,playidx
	playidx -= 1
	if playidx < 0:
		playqueue = playlist
		playidx = len(playqueue)-1 if playqueue else 0
	play_idx()

def next_song():
	global playlist,playqueue,playidx
	playidx += 1
	if playidx >= len(playqueue):
		playqueue = playlist
		playidx = 0
	play_idx()

def update_url():
	global playqueue,playidx
	if playidx >= len(playqueue):
		return False
	song = playqueue[playidx]
	search = '%s %s' % (song.name,song.artist)
	try:
		s = next(gs.search(search, type=Client.SONGS))
		song.stream.url = s.stream.url
		return True
	except StopIteration:
		return False

def queue_songs(songs):
	songs = list(songs)
	if not songs:
		return
	global playqueue,playidx
	playqueue = playqueue[:playidx+1] + songs + playqueue[playidx+1:]
	next_song()

class FileSong:
	def __init__(self, _name,_artist,_url):
		self.name = _name
		self.artist = _artist
		class Stream:
			pass
		self.stream = Stream()
		self.stream.url = _url

def load_list():
	songs = []
	if not os.path.exists(listname+'.txt'):
		return songs
	for line in open(listname+'.txt', 'rt'):
		try:
			artist,songname,url = [w.strip() for w in line.split(',')]
			songs += [FileSong(songname,artist,url)]
		except:
			pass
	return songs

def save_list(songlist):
	f = open(listname+'.txt', 'wt')
	f.write('Playlist for AidBand. Each line contains artist, song name and URL. The first two can be left empty if file:// and otherwise the URL should be left empty if GrooveShark.\n')
	for song in songlist:
		f.write('%s, %s,\n' % (song.artist, song.name))

def _pfixs(s):
	return str(s).encode().decode('cp850', 'ignore')

def _match_ratio(s1,s2):
	return difflib.SequenceMatcher(None,s1.lower(),s2.lower()).ratio()


try: os.mkdir('cache')
except: pass
gs = Client()
gs.init()
play_list(hotoptions.My)
while True:
	try:
		print('Enter search term:')
		cmd = None
		while not cmd:
			poll()
			time.sleep(0.3)
			cmd = keypeeker.peekstr()
		if cmd == '<quit>':
			stop()
			sys.exit(0)
		fkeys = re.findall(r'<F(\d+)>',cmd)
		if fkeys:
			fkey_idx = int(fkeys[-1])-1
			if len(hotoptions.all) > fkey_idx:
				ln = hotoptions.all[fkey_idx]
				print(ln)
				play_list(ln)
		elif cmd == '+':
			add_song()
			print('Song added to %s.' % listname)
		elif cmd == '-':
			drop_song()
			print('Song dropped from %s.' % listname)
		elif cmd == '<Up>':
			prev_song()
		elif cmd == '<Down>':
			next_song()
		elif cmd.endswith('\r'):
			searchterm = cmd.rstrip('\r')
			print(searchterm)
			play_search(searchterm)
	except Exception as e:
		traceback.print_exc()
		print(e)
