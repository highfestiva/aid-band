#!/usr/bin/env python3

import codecs
import difflib
import glob
import spotipy

sp = spotipy.Spotify()

def _almost_same(s1,s2):
	s1,s2 = s1.lower(),s2.lower()
	return s1 in s2 or difflib.SequenceMatcher(None,s1,s2).ratio() >= 0.8

def gettracks(artist):
	hits = sp.search(artist)
	tracks = hits['tracks']['items']
	ts = []
	for t in tracks:
		exact_artists = [a for a in t['artists'] if _almost_same(artist, a['name'])]
		for a in exact_artists:
			ts += ['%s ~ %s ~' % (t['artists'][0]['name'],t['name'])]
		if not exact_artists:
			# Perhaps some cover can lead us on the path...
			ts += ['%s ~ %s ~' % (artist,t['name'])]
	return ts

files = [f for f in glob.glob('*.txt') if 'todo' not in f]
for f in files:
	lines = [l for l in codecs.open(f,'r','utf-8')]
	newtracks = 0
	newlines = []
	for line in lines:
		line = line.strip()
		if len(line) >=3 and len(line) < 30 and ',' not in line and '#' not in line and '~' not in line:
			# Probably an artist.
			tracks = gettracks(line)
			newlines += tracks if tracks else [line]
			newtracks += len(tracks)
		else:
			newlines += [line]
	if newlines == lines:
		print('%s - not touched' % f)
	else:
		w = codecs.open(f,'w','utf-8')
		[w.write(l+'\n') for l in newlines]
		print('%s - %i tracks added' % (f,newtracks))
