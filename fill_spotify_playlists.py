#!/usr/bin/env python3
#Uses spotipy to fill the playlists. Enter a bunch of artists in your playlists
#(no ~'s on those lines), and some songs by each artist will be added.

import codecs
import difflib
import glob
import spotipy
import sys

sp = spotipy.Spotify()

def _almost_same(s1,s2):
	s1,s2 = s1.lower(),s2.lower()
	return s1 in s2 or difflib.SequenceMatcher(None,s1,s2).ratio() >= 0.8

def gettracks(artist, track):
	hits = sp.search(' '.join([track,artist]))
	tracks = hits['tracks']['items']
	ts = []
	for t in tracks:
		exact_artists = [a for a in t['artists'] if _almost_same(artist, a['name'])]
		for a in exact_artists:
			ts += ['%s ~ %s ~ %s' % (t['artists'][0]['name'],t['name'],t['uri'])]
		if not exact_artists:
			# Perhaps some cover can lead us on the path...
			ts += ['%s ~ %s ~ %s' % (artist,t['name'],t['uri'])]
		if track and ts:
			break
	return ts

globs = glob.glob('*.txt' if not sys.argv[1:] else sys.argv[1])
files = [f for f in globs if 'todo' not in f]
for f in files:
	lines = [l for l in codecs.open(f,'r','utf-8')]
	newtracks = 0
	newlines = []
	for line in lines:
		line = line.strip()
		if len(line) >= 2 and len(line) < 30 and ',' not in line and '#' not in line and '~' not in line:
			# Probably an artist.
			tracks = gettracks(line, '')
			newlines += tracks if tracks else [line]
			newtracks += len(tracks)
		elif '~' in line and ('http' not in line and 'spotify:' not in line):
			artist,track,uri = [w.strip() for w in line.split('~')]
			tracks = gettracks(artist,track)
			newlines += [tracks[0]] if tracks else [line]
			newtracks += 1 if tracks else 0
		else:
			newlines += [line]
	if newlines == lines or not newtracks:
		print('%s - not touched' % f)
	else:
		w = codecs.open(f,'w','utf-8')
		[w.write(l+'\n') for l in newlines]
		w.close()
		print('%s - %i tracks added' % (f,newtracks))
