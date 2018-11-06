#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import html
import os
import pafy
import re
import subprocess
import urllib.parse


pages = re.compile(r'q=(http.*?://[a-z\.-_]*?youtube\.com/watch%3Fv%3D.+?)&.*?>(.*?)</a>')
tags = re.compile(r'<.*?>')
parenths = re.compile(r'(.*?)\((.*?)\)(.*)')
bad_words = 'album official video music'.split()


def search(s):
    param = urllib.parse.urlencode({'q': 'site:youtube.com %s' % s})
    url = 'https://www.google.se/search?%s' % param
    body = subprocess.check_output('curl -H "user-agent: Mozilla/5.0" %s' % url, shell=True, stderr=subprocess.DEVNULL).decode()
    artist = ''
    songs = []
    urls = set()
    names = set()
    hits = []
    for pagelink in pages.finditer(body):
        url = pagelink.group(1).replace('%3F','?').replace('%3D', '=')
        name = html.unescape(pagelink.group(2))
        name = name.encode().partition(b'\xe2')[0].decode()
        name = tags.sub(' ', name)
        r = parenths.match(name)
        if r:
            name = r.group(1) + ' ' + r.group(3)
            inparenths = r.group(2).strip()
            if inparenths.lower() in s.lower():
                name += ' ' + inparenths
        name = name.partition('(')[0]
        name = name.replace('"', ' ').replace('`', "'").strip(' \t-+"\'=!.')
        words = [w for w in name.split() if not [b for b in bad_words if b in w.lower()]]
        name = ' '.join(words).strip()
        if not name:
            continue
        exists = (url in urls or name in names)
        urls.add(url)
        names.add(name)
        if exists:
            continue
        hits.append([name,url])
    # place those with dashes (-) first, assumed to be better named
    hits = sorted(hits, key=lambda nu: nu[0].index('-') if '-' in nu[0] else +100)
    # sort by exact match, word by word
    words = s.lower().replace('-',' ').split()
    hits = sorted(hits, key=lambda nu: -sum((n==w) for n,w in zip(nu[0].lower().replace('-', ' ').split(), words)))
    # 1st pick artist if present in any hit
    artists = [] # ordered; don't use set()
    for name,url in hits:
        words = [w.strip() for w in name.split('-') if 'youtube' not in w.lower()]
        if len(words) == 2:
            artist = words[0].strip()
            if artist not in artists:
                artists.append(artist)
    # ok, lets add up the songs (using the artist stated by any of the songs previously)
    for name,url in hits:
        words = [w.strip() for w in name.split('-') if 'youtube' not in w.lower()]
        if len(words) == 2:
            artist = words[0].strip()
            song = words[1].strip()
            songs += [ABSong(song, artist, url)]
        elif len(words) == 1:
            song = words[0]
            for artist in artists:
                artist_index = song.lower().find(artist.lower())
                if artist_index >= 0:
                    song = (song[:artist_index].strip() + ' ' + song[artist_index+len(artist):].strip()).strip()
                    if song:
                        songs += [ABSong(song, artist, url)]
                    break
            else:
                songs += [ABSong(song, s, url)]
    return songs


def cache_song(url, wildcard):
    if 'youtube.com' in url:
        video = pafy.new(url)
        audiostream = max(video.audiostreams, key=lambda audio: abs(audio.rawbitrate-131072))
        if audiostream.get_filesize() > 8e6:
            print('File too big, refusing to download!')
            return ''
        src_filename = audiostream.download()
        print()
        base,ext = os.path.splitext(src_filename)
        dst_filename = wildcard.replace('.*', ext)
        os.rename(src_filename, dst_filename)
        return dst_filename


if __name__ == '__main__':
    songs = search('milencolin')
    print(songs)
    cache_song(songs[0].uri, './something.*')
