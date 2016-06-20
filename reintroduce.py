#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''Reintroduces songs that are currently cached, but not in any playlist, into the favorites playlist.'''


from codecs import open
from collections import defaultdict
from glob import glob

playlists = [
	['classical', 'sonata mozart händel chopin beethoven orff minor fugue adagio piano concerto nocturne'.split()],
	['meditation', 'meditation yoga buddhist monks chant mantra tibet meredith healing llama lama buddha'.split()],
	['christmas', 'jul, julen x-mas christmas'.split()],
	['favorites', ['']]
]

addit = defaultdict(dict)

song_file_map = {}
files = [f.replace('\\','/') for f in glob('cache/*.ogg')]
for fname in files:
	at = fname.split('/',1)[1].rsplit('.ogg',1)[0]
	artist,track = at.split('-',1)
	if len(artist) <= 2:
		artist,track = at.rsplit('-',1)
	song_file_map[artist+' ~ '+track] = fname

all_songs = set([l.rsplit(' ~ ',1)[0].lower() for f in glob('*.txt') for l in open(f,encoding='utf8') if ' ~ ' in l])

reintroduced = 0
for track,fn in song_file_map.items():
	if track.lower() not in all_songs:
		reintroduced += 1
		skip = False
		for playlist,kws in playlists:
			for kw in kws:
				if kw in track.lower():
					addit[playlist][track] = fn
					skip = True
					break
			if skip:
				break

for playlist,tracks in addit.items():
	print(playlist)
	f = open(playlist+'.txt', 'a', encoding='utf8')
	for track,fn in tracks.items():
		print(track+' ~ ', file=f)
	
print('Reintroduced %i %% songs.' % (reintroduced*100//len(song_file_map)))
