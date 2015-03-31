#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import argparse
import codecs
import difflib
from grooveshark import Client
import hotoptions
import interruptor
import keypeeker
import netpeeker
import os.path
import random
import re
import sr_radio
import speech
import subprocess
import threading
import time
import traceback


proc = None
start_play_time = time.time()
cache_write_name = None
gs = None
allowcache = False
useshuffle = True
listname = None
playlist = []
playqueue = []
shuffleidx = []
ishits = False
playidx = 0
datadir = '.'


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

def remove_from_cache(song):
	fn = _confixs(_cachename(song))
	if os.path.exists(fn):
		os.remove(fn)

def play_idx():
	global playqueue
	if playidx < len(playqueue):
		song = playqueue[shuffleidx[playidx]]
		output(song.artist, '-', song.name)
		if song in playlist and 'radio' not in listname:
			fn = _cachename(song)
			url = fn if os.path.exists(_confixs(fn)) else song.stream.url
		else:
			fn = None
			url = song.stream.url
		if not url:
			update_url()
			url = song.stream.url
		play_url(url, fn)
		# Once played the song expires, no use attempting to play that URL again.
		song = ABSong(song.name,song.artist,None)
		playqueue[shuffleidx[playidx]] = song

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

def raw_play_list(name, doplay=True):
	global listname
	listname = name
	global playlist,playqueue,playidx,shuffleidx,ishits
	doshuffle = useshuffle
	if listname == hotoptions.Hit:
		ishits = True
		playqueue = list(gs.popular())
		listname = hotoptions.Favorites
		playlist = load_list()
		doshuffle = False
	else:
		ishits = False
		playlist = load_list()
		playqueue = playlist[:]
		if 'radio' in listname:
			doshuffle = False
	shuffleidx = list(range(len(playqueue)))
	if doshuffle:
		random.shuffle(shuffleidx)
	playidx = 0
	_validate()
	if doplay:
		if playqueue:
			play_idx()
		else:
			stop()
	return playqueue

def play_list(name):
	pq = raw_play_list(name)
	if pq:
		avoutput(_simple_listname())
	else:
		avoutput('%s playlist is empty, nothing to play.' % _simple_listname())

def search_queue(search):
	match = lambda s: max(_match_ratio(s.name,search),_match_ratio(str(s.artist),search))
	ordered = sorted(playqueue, key=match, reverse=True)
	if ordered:
		song = ordered[0]
		if match(song) > 0.8:
			return song
	return None

def search_music(search):
	songs = []
	try:
		artists = sorted(gs.search(search, type=Client.ARTISTS), key=lambda a: _match_ratio(a.name, search), reverse=True)
		if artists:
			# Get exact artist match if possible.
			arts = [a for a in artists if a.name.lower() == search.lower()]
			artists = arts if arts else artists
			# Add most popular songs, and see which one we're after.
			arts = []
			ss = {}
			for a in artists[:5]:
				score,i = 0,0
				for s in a.songs:
					score += int(s.popularity)
					i += 1
					if i >= 10:
						break
				arts += [(a,score)]
			artist = sorted(arts, key=lambda l:l[1], reverse=True)[0][0]
			# If searching for artist, pick a bunch of songs, sort by popularity and remove redundant.
			ss = sorted(artist.songs, key=lambda s: int(s.popularity), reverse=True)
			# Uniquify.
			names = set()
			for s in ss[:50]:
				if s.name not in names:
					names.add(s.name)
					songs.append(s)
			songs = songs[:20]
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
		song = search_queue(search)
		if song:
			global playidx
			idx = playqueue.index(song)
			playidx = shuffleidx.index(idx)
			play_idx()
			return
		songs = search_music(search)
	if not songs:
		avoutput('Nothing found, try again.')
	queue_songs(songs)

def add_song():
	global playlist,playqueue
	if shuffleidx[playidx:playidx+1]:
		song = playqueue[shuffleidx[playidx]]
		if song not in playlist:
			playlist += [song]
			save_list(playlist)
			avoutput('%s added to %s.' % (song.name,_simple_listname()))
			return True
		else:
			avoutput('%s already in %s.' % (song.name,_simple_listname()))
	else:
		avoutput('Play queue is empty, no song to add.')
	_validate()

def drop_song():
	global playlist,playqueue,shuffleidx
	if playidx < len(shuffleidx):
		pqidx = shuffleidx[playidx]
		song = playqueue[pqidx]
		playqueue = playqueue[:pqidx] + playqueue[pqidx+1:]
		shuffleidx = shuffleidx[:playidx] + shuffleidx[playidx+1:]
		shuffleidx = [s if s<pqidx else s-1 for s in shuffleidx]	# Reduce all above a certain index.
		playlist = list(filter(lambda s: s!=song, playlist))
		play_idx()
		save_list(playlist)
		remove_from_cache(song)
		avoutput('%s dropped from %s.' % (song.name,_simple_listname()))
		return True
	else:
		avoutput('Play queue is empty, no song to remove.')
	_validate()

def prev_song():
	global playqueue,playidx
	playidx -= 1
	if playidx < 0:
		playidx = len(playqueue)-1 if playqueue else 0
	play_idx()

def next_song():
	global playqueue,playidx
	playidx += 1
	if playidx >= len(playqueue):
		playidx = 0
	play_idx()

def update_url():
	global playqueue,playidx
	if playidx >= len(playqueue):
		return False
	song = playqueue[shuffleidx[playidx]]
	search = '%s %s' % (song.name,song.artist)
	try:
		s = next(gs.search(search, type=Client.SONGS))
		song.stream.url = s.stream.url
		return True
	except StopIteration:
		return False

def execute(cmd):
	cmd,params = [c.strip() for c in cmd.split(':')]
	if cmd == 'say':
		speech.say(params)
	if cmd == 'pwr' and params == 'off':
		import win32api
		win32api.ExitWindowsEx(24,0)

def queue_songs(songs):
	songs = list(songs)
	if not songs:
		return
	global playqueue,playidx,shuffleidx
	newidx = list(range(len(playqueue),len(playqueue)+len(songs)))
	playqueue += songs
	shuffleidx = shuffleidx[:playidx+1] + newidx + shuffleidx[playidx+1:]
	_validate()
	next_song()

def load_list():
	songs = []
	fn = os.path.join(datadir,listname+'.txt')
	if not os.path.exists(fn):
		return songs
	for line in codecs.open(fn, 'r', 'utf-8'):
		try:
			artist,songname,url = [w.strip() for w in line.split('~')]
			songs += [ABSong(songname,artist,url)]
		except:
			pass
	return songs

def save_list(songlist):
	fn = os.path.join(datadir,listname+'.txt')
	f = codecs.open(fn, 'w', 'utf-8')
	f.write('Playlist for AidBand. Each line contains artist, song name and URL. The first two can be left empty if file:// and otherwise the URL should be left empty if GrooveShark.\n')
	for song in songlist:
		f.write('%s ~ %s ~ %s\n' % (song.artist, song.name, song.stream.url if 'radio' in listname else ''))

def output(*args):
	s = ' '.join([str(a) for a in args])
	print(s.encode('cp850','ignore').decode('cp850'))
	netpeeker.output(s)

def avoutput(*args):
	s = ' '.join([str(a) for a in args])
	output(s)
	speech.say(s)

def _validate():
	if not ishits:
		assert len(playqueue) >= len(playlist)
	assert len(playqueue) == len(shuffleidx)
	for i in range(len(playqueue)):
		assert shuffleidx[i] < len(playqueue)
	assert playidx < len(shuffleidx) or len(shuffleidx) == 0

def _simple_listname():
	return listname.split('_')[-1]

def _cachename(song):
	return os.path.join(datadir, 'cache/'+(str(song.artist)+'-'+song.name+'.mpeg').lower().replace(' ','_').replace('/','_').replace('\\','_'))

def _confixs(s):
	return '_'.join(str(s).encode().decode('ascii', 'ignore').split('?'))

def _match_ratio(s1,s2):
	return difflib.SequenceMatcher(None,s1.lower(),s2.lower()).ratio()


parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', dest='datadir', metavar='DIR', default='.', help="directory containing playlists and cache (default is '.')")
parser.add_argument('--without-grooveshark', dest='nogs', action='store_true', default=False, help="don't login to music service, meaning only radio can be played")
options = parser.parse_args()

datadir = options.datadir
try: os.mkdir(os.path.join(datadir,'cache'))
except: pass

tid = threading.current_thread().ident
event = threading.Event()
def handle_keys(k):
	interruptor.handle_keys(tid,k)
	event.set()
keypeeker.init(handle_keys)
netpeeker.init(handle_keys)
try:
	if not options.nogs:
		gs = Client()
		gs.init()
except Exception as e:
	traceback.print_exc()
	print('Exception during startup:', e)
raw_play_list(hotoptions.Favorites, doplay=False)

stopped = True
while True:
	try:
		output('Enter search term:')
		cmd = ''
		while not cmd:
			event.wait(2)
			time.sleep(0.01)	# Hang on a pinch to see if there's more to be had.
			if not stopped:
				poll()
			cmd = keypeeker.peekstr() + netpeeker.peekstr()
		if cmd == '<quit>':
			stop()
			netpeeker.stop()
			keypeeker.stop()
			import win32process
			win32process.ExitProcess(0)
		if cmd == '<F12>':
			stopped = not stopped
			if stopped:
				stop()
				output('Audio stopped.')
			else:
				play_idx()
			continue
		fkeys = re.findall(r'<F(\d+)>',cmd)
		if fkeys:
			fkey_idx = int(fkeys[-1])-1
			if len(hotoptions.all) > fkey_idx:
				ln = hotoptions.all[fkey_idx]
				play_list(ln)
				stopped = False
		elif cmd == '+':
			add_song()
		elif cmd == '-':
			if drop_song():
				stopped = False
		elif cmd == '<Left>':
			prev_song()
			stopped = False
		elif cmd == '<Right>':
			next_song()
			stopped = False
		elif cmd == '\t':
			useshuffle = not useshuffle
			if shuffleidx:
				curidx = shuffleidx[playidx]
				shuffleidx = list(range(len(playqueue)))
				if useshuffle:
					random.shuffle(shuffleidx)
				playidx = shuffleidx.index(curidx)
				avoutput('Shuffle.' if useshuffle else 'Playing in order.')
			_validate()
		elif cmd.endswith('\r'):
			cmd = cmd.strip()
			if len(cmd) < 2:
				output('Too short search string "%s".' % cmd)
				continue
			output(cmd)
			if ':' not in cmd:
				play_search(cmd)
				stopped = False
			else:
				execute(cmd)
	except TypeError as te:
		for a in te.args:
			if 'list indices' in a:
				stop()
				stopped = True
				avoutput("You're banned from Groove Shark!")
				break
	except Exception as e:
		try:
			traceback.print_exc()
			output(e)
			keypeeker.getstr()	# Clear keyboard.
			netpeeker.getstr()	# Clear remote keyboard.
		except:
			pass
