#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from hotoptions import hotoptions
import grooveshark
import keypeeker
import re
import subprocess
import time

proc = None
playlist = []
playqueue = []
playidx = 0

def play_url(url):
	global proc
	print('Killing...')
	if proc:
		proc.kill()
	print('Starting new process...')
	proc = subprocess.Popen(['mplayer.exe', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	print('Started.')

def play_idx():
	global playqueue,playidx
	if playidx < len(playqueue):
		song = playqueue[playidx]
		play_url(song.stream.url)

def play_list(name):
	print(name)

def play_search(search):
	global playqueue,playidx
	songs = list(gs.search(search))
	if songs:
		playqueue = playqueue[:playidx+1] + songs + playqueue[playidx+1:]
		next_song()

def add_song():
	global playlist,playqueue,playidx
	if playqueue[playidx:playidx+1]:
		playlist += playqueue[playidx:playidx+1]

def drop_song():
	global playlist,playqueue,playidx
	if playidx < len(playqueue):
		song = playqueue[playidx]
		playlist = list(filter(lambda s: s!=song, playlist))

def prev_song():
	global playlist,playqueue,playidx
	playidx -= 1
	if playidx < 0:
		playqueue = playlist
		playidx = 0
	play_idx()

def next_song():
	global playlist,playqueue,playidx
	playidx += 1
	if playidx >= len(playqueue):
		playqueue = playlist
		playidx = 0
	play_idx()


gs = grooveshark.Client()
gs.init()
while True:
	print('Enter search term:')
	cmd = None
	while not cmd:
		time.sleep(0.1)
		cmd = keypeeker.peekstr()
	print(cmd)
	fkeys = re.findall(r'<F(\d+)>',cmd)
	if fkeys:
		fkey = int(fkeys[-1])
		if len(hotoptions) > fkey:
			play_list(hotoptions[fkey])
	elif cmd == '+':
		adds_song()
	elif cmd == '-':
		drop_song()
	elif cmd == '<Up>':
		prev_song()
	elif cmd == '<Down>':
		next_song()
	elif cmd.endswith('\r'):
		searchterm = cmd.rstrip('\r')
		play_search(searchterm)
