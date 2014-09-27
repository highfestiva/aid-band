#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import codecs
import difflib
from grooveshark import Client
import hotoptions
import keypeeker
import os.path
import sr_radio
import re
import speech
import subprocess
import sys
import time
import traceback


proc = None
start_play_time = time.time()
cache_write_name = None
gs = None
allowcache = False
listname = None
playlist = []
playqueue = []
playidx = 0


def stop():
	global proc,cache_write_name
	if proc:
		proc.kill()
		proc.wait()
		if cache_write_name:
			try: os.remove(_confixs(cache_write_name))
			except: pass
			cache_write_name = None

def play_url(url, cachename):
	stop()
	global proc,start_play_time,cache_write_name
	cache_write_name = None
	if cachename and url.startswith('http') and allowcache:
		cmd = ['mplayer.exe', url, '-dumpstream', '-dumpfile', _confixs(cachename)]
		cache_write_name = cachename
	elif not url.startswith('http'):
		cmd = ['mplayer.exe', _confixs(url)]
	else:
		cmd = ['mplayer.exe', url]
	proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	start_play_time = time.time()

def play_idx():
	global playqueue,playidx
	if playidx < len(playqueue):
		song = playqueue[playidx]
		print(_confixs(song.artist), '-', _confixs(song.name))
		if song in playlist and 'radio' not in listname:
			fn = ('cache_%s/' % listname)+(str(song.artist)+'-'+song.name+'.mpeg').lower().replace(' ','_').replace('/','_').replace('\\','_')
			url = fn if os.path.exists(_confixs(fn)) else song.stream.url
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
	global cache_write_name
	if cache_write_name and os.path.exists(_confixs(cache_write_name)):
		cache_write_name = None
		play_idx()	# Play from cache.
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
		listname = hotoptions.Favorites
		playlist = load_list()
	else:
		playlist = playqueue = load_list()
	playidx = 0
	if playqueue:
		play_idx()
		speech.say(_simple_listname())
	else:
		stop()
		speech.say('%s playlist is empty, nothing to play.' % _simple_listname())

def search_music(search):
	songs = []
	try:
		artists = sorted(gs.search(search, type=Client.ARTISTS), key=lambda a: _match_ratio(a.name, search), reverse=True)
		if artists:
			# Get exact artist match if possible.
			arts = [a for a in artists if a.name.lower() == search]
			artists = arts if arts else artists
			# Add most popular songs, and see which one we're after.
			arts = []
			ss = {}
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
					songs += [s.name,artist.name,s.stream.url]
			songs = songs[:30]
	except StopIteration:
		try:
			# If searching for songs, just pick first hit.
			songs = [next(gs.search(search, type=Client.SONGS))]
		except StopIteration:
			pass
	return songs

def play_search(search):
	if 'radio' in listname:
		songs = sr_radio.search(search)
	else:
		songs = search_music(search)
	if not songs:
		speech.say('Nothing found, try again.')
	queue_songs(songs)

def add_song():
	global playlist,playqueue,playidx
	if playqueue[playidx:playidx+1]:
		song = playqueue[playidx]
		playlist += [song]
		save_list(playlist)
		speech.say('%s added to %s.' % (song.name,_simple_listname()))
	else:
		speech.say('Play queue is empty, no song to add.')

def drop_song():
	global playlist,playqueue,playidx
	if playidx < len(playqueue):
		song = playqueue[playidx]
		playqueue = playqueue[:playidx] + playqueue[playidx+1:]
		playlist = list(filter(lambda s: s!=song, playlist))
		play_idx()
		save_list(playlist)
		speech.say('%s dropped from %s.' % (song.name,_simple_listname()))
	else:
		speech.say('Play queue is empty, no song to remove.')

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

def execute(cmd):
	cmd,params = cmd.split(':')
	if cmd == 'say':
		speech.say(params)

def queue_songs(songs):
	songs = list(songs)
	if not songs:
		return
	global playqueue,playidx
	playqueue = playqueue[:playidx+1] + songs + playqueue[playidx+1:]
	next_song()

def load_list():
	songs = []
	if not os.path.exists(listname+'.txt'):
		return songs
	for line in codecs.open(listname+'.txt', 'r', 'utf-8'):
		try:
			artist,songname,url = [w.strip() for w in line.split('~')]
			songs += [ABSong(songname,artist,url)]
		except:
			pass
	return songs

def save_list(songlist):
	f = codecs.open(listname+'.txt', 'w', 'utf-8')
	f.write('Playlist for AidBand. Each line contains artist, song name and URL. The first two can be left empty if file:// and otherwise the URL should be left empty if GrooveShark.\n')
	for song in songlist:
		f.write('%s ~ %s ~ %s\n' % (song.artist, song.name, song.stream.url if 'radio' in listname else ''))

def _simple_listname():
	return listname.split('_')[-1]

def _confixs(s):
	return '_'.join(str(s).encode().decode('ascii', 'ignore').split('?'))

def _match_ratio(s1,s2):
	return difflib.SequenceMatcher(None,s1.lower(),s2.lower()).ratio()


for ch in hotoptions.all:
	if 'radio' not in ch:
		try: os.mkdir('cache_'+str(ch))
		except: pass

try:
	if 'nogs' not in sys.argv:
		gs = Client()
		gs.init()
	play_list(hotoptions.Favorites)
except:
	pass

stopped = False
while True:
	try:
		print('Enter search term:')
		cmd = None
		while not cmd:
			if stopped:
				time.sleep(2)
			else:
				time.sleep(0.3)
				poll()
			cmd = keypeeker.peekstr()
		if cmd == '<quit>':
			stop()
			sys.exit(0)
		if cmd == '<F12>':
			stopped = not stopped
			stop() if stopped else play_idx()
			continue
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
			stopped = False
			print('Song dropped from %s.' % listname)
		elif cmd == '<Up>':
			prev_song()
			stopped = False
		elif cmd == '<Down>':
			next_song()
			stopped = False
		elif cmd.endswith('\r'):
			cmd = cmd.rstrip('\r')
			print(cmd)
			if ':' not in cmd:
				play_search(cmd)
				stopped = False
			else:
				execute(cmd)
	except Exception as e:
		traceback.print_exc()
		print(e)
