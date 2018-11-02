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


def search(s):
    print(s)
    param = urllib.parse.urlencode({'q': 'site:youtube.com %s' % s})
    url = 'https://www.google.se/search?%s' % param
    body = subprocess.check_output('curl -H "user-agent: Mozilla/5.0" %s' % url, shell=True, stderr=subprocess.DEVNULL).decode()
    artist = ''
    songs = []
    urls = set()
    names = set()
    for pagelink in pages.finditer(body):
        url = pagelink.group(1).replace('%3F','?').replace('%3D', '=')
        name = html.unescape(pagelink.group(2))
        while True:
            try:
                i = name.lower().index('youtube')
                name = name[:i] + ' ' + name[i+7:]
            except:
                break
        name = name.encode().partition(b'\xe2')[0].decode()
        name = tags.sub(' ', name)
        r = parenths.match(name)
        if r:
            name,inparenths = r[1],r[2].strip()
            name += r[3]
            if inparenths.lower() in s.lower():
                name += ' ' + inparenths
        name = name.partition('(')[0]
        name = name.replace('"', ' ').replace('`', "'").strip(' \t-+"\'=!.')
        name = ' '.join(name.split())
        if not name:
            continue
        exists = (url in urls or name in names)
        urls.add(url)
        names.add(name)
        if exists:
            continue
        words = [w.strip() for w in name.split('-') if 'youtube' not in w.lower()]
        if len(words) == 2:
            artist = words[0]
            song = words[1]
            songs += [ABSong(song, artist, url)]
        elif len(words) == 1:
            song = words[0]
            artist_index = song.lower().find(artist.lower())
            if artist and artist_index >= 0:
                song = song[:artist_index].strip() + ' ' + song[artist_index+len(artist):].strip()
                songs += [ABSong(song, artist, url)]
            else:
                songs += [ABSong(song, s, url)]
    return songs


def cache_song(url, wildcard):
    if 'youtube.com' in url:
        video = pafy.new(url)
        audiostream = max(video.audiostreams, key=lambda audio: abs(audio.rawbitrate-131072))
        src_filename = audiostream.download()
        base,ext = os.path.splitext(src_filename)
        dst_filename = wildcard.replace('.*', ext)
        os.rename(src_filename, dst_filename)
        return dst_filename


if __name__ == '__main__':
    songs = search('milencolin')
    print(songs)
    cache_song(songs[0].uri, './something.*')
