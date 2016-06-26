#!/usr/bin/env python3

from collections import defaultdict
from codecs import open
from glob import glob

song_file = {}
files = [f.replace('\\','/') for f in glob('cache/*.ogg')]
for fname in files:
	at = fname.split('/',1)[1].rsplit('.ogg',1)[0].replace('_','/')
	artist,track = at.split('-',1)
	if len(artist) <= 2:
		artist,track = at.rsplit('-',1)
	song_file[artist+' ~ '+track] = fname

all_songs = set([l for f in glob('*.txt') for l in open(f,encoding='utf8') if ' ~ ' in l])
all_songs = [[w.strip() for w in l.split('~')] for l in all_songs ]

uri_songs = defaultdict(set)
for artist,track,uri in all_songs:
	if uri:
		uri_songs[uri].add((artist, track, uri))

remove_songs = []
for uri,songs in uri_songs.items():
	if len(songs) <= 1:
		continue
	cached_songs = [(a+' ~ '+t) for a,t,u in songs if a+' ~ '+t in song_file]
	if not cached_songs:
		continue
	assert len(cached_songs) < 2
	keep = cached_songs[0]
	uncached_songs = [(a+' ~ '+t) for a,t,u in songs if a+' ~ '+t not in cached_songs]
	remove_songs += [(rem,keep) for rem in uncached_songs]

for f in glob('*.txt'):
	lines = [line.strip() for line in open(f,encoding='utf8')]
	newlines = lines[:]
	for rem,keep in remove_songs:
		newlines = [line for line in newlines if not line.startswith(rem)]
	if newlines != lines:
		print('Removed %i duplicates from %s.' % (len(lines)-len(newlines),f))
		open(f,'w',encoding='utf8').write('\n'.join(newlines)+'\n')
