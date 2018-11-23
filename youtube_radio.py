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
bad_urls = 'list= /channel/'.split()
bad_names = 'review'.split()
drop_words = 'album official video music youtube'.split()
clean_ends = lambda s: s.strip(' \t-+"\'=!.')


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
        name = name.replace('~', ' - ').replace(':', ' - ').replace('"', ' ').replace('`', "'")
        # print(name, url)
        if _match_words(url, bad_urls) or _match_words(name, bad_names):
            continue
        words = [w for w in name.split() if not [b for b in drop_words if b in w.lower()]]
        name = ' '.join(words).strip()
        name = clean_ends(name)
        if not name:
            continue
        exists = (url in urls or name in names)
        urls.add(url)
        names.add(name)
        if exists:
            continue
        hits.append([name,url])
    # sort by length
    hits = sorted(hits, key=lambda nu: len(nu[0]))
    # place those with dashes (-) first, assumed to be better named
    hits = sorted(hits, key=lambda nu: nu[0].index('-') if '-' in nu[0] else +100)
    # sort by exact match, phrase by phrase + additional points for the correct order
    search_phrases = [p.strip() for p in s.lower().split('-')]
    matchlen_pos = lambda s1,s2,p1,p2: len(os.path.commonprefix([s1,s2])) * (2 if p1==p2 else 1)
    score_phrase = lambda nu: -sum(max([matchlen_pos(pn.strip(), pp, i, j) for j,pp in enumerate(search_phrases)]) for i,pn in enumerate(nu[0].lower().split('-')))
    hits = sorted(hits, key=score_phrase)
    # print('\n'.join(str(h) for h in hits))
    # print()
    # cleanup names
    for i,(name,url) in enumerate(hits):
        r = parenths.match(name)
        if r:
            words = [r.group(1), r.group(3)]
            inparenths = r.group(2).strip()
            if inparenths.lower() in s.lower():
                words += [inparenths]
            name = clean_ends(' '.join(w.strip() for w in words))
            hits[i][0] = name
    # print('\n'.join(str(h) for h in hits))
    # 1st pick artist if present in any hit
    artists = [] # ordered; don't use set()
    for name,url in hits:
        words = [w.strip() for w in name.split('-')]
        if len(words) >= 2:
            artist = words[0].strip()
            if artist not in artists:
                artists.append(artist)
    # ok, lets add up the songs (using the artist stated by any of the songs previously)
    known_songname = s.partition('-')[2].strip()
    for name,url in hits:
        words = [w.strip() for w in name.split('-')]
        if len(words) >= 2:
            artist = words[0]
            song = words[1]
            for i in range(2, len(words)):
                if known_songname and words[i].lower().startswith(known_songname.lower()):
                    song = words[i]
                    break
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
    # print(songs)
    # os._exit(1)
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


def _match_words(s, words):
    return any((word in s.lower()) for word in words)


if __name__ == '__main__':
    songs = search('milencolin')
    print(songs)
    cache_song(songs[0].uri, './something.*')
