#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import os
import pafy
import re
import subprocess
import urllib.parse


pages = re.compile(r'(http.*?://[a-z\.-_]*?youtube\.com/watch?v=.+)".*?>(.*?)<')


def search(s):
    print(s)
    param = urllib.parse.urlencode({'q': 'site:youtube.com %s' % s})
    url = 'https://www.google.se/search?%s' % param
    html = subprocess.check_output('curl -H "user-agent: Mozilla/5.0" %s' % url, shell=True, stderr=subprocess.DEVNULL).decode()
    artist = ''
    songs = []
    for pagelink in pages.finditer(html):
        url = pagelink.group(1)
        name = pagelink.group(2)
        words = [w.strip() for w in name.split('-') if 'youtube' not in w.lower()]
        if len(words) == 2:
            artist = words[0]
            song = words[1].split('(')[0]
            songs += [ABSong(song, artist, url)]
        elif len(words) == 1:
            song = words[0]
            artist_index = artist.lower() in song.lower().find(artist.lower())
            if artist and artist_index >= 0:
                song = song[:artist_index].strip() + ' ' + song[artist_index+len(artist):].strip()
                songs += [ABSong(song, artist, url)]
            else:
                songs += [ABSong(song, s, url)]
    return songs


def cache_song(url, wildcard):
    if 'https://youtube.com' in url:
        video = pafy.new(url)
        audiostream = max(video.audiostreams, key=lambda audio: abs(audio.rawbitrate-131072))
        src_filename = audiostream.download()
        base,ext = os.path.splitext(filename)
        dst_filename = wildcard.replace('.*', ext)
        os.rename(src_filename, dst_filename)
        return dst_filename


songs = search('Kim Cesarion')
cache_song(songs[0], './something.*')
