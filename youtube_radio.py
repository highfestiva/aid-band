#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import html
import os
import pafy
import re
import subprocess
import urllib.parse
from urllib.parse import urlencode, unquote as urldecode


pages = re.compile(r'"nofollow" .+(https.*?youtube\.com%2Fwatch.+?)&.*?>(.*?)</a>')
tags = re.compile(r'<.*?>')
parenths = re.compile(r'(.*?)\((.*?)\)(.*)')
bad_urls = 'list= /channel/'.split()
bad_names = 'review'.split()
drop_words = 'album official video music youtube https'.split()
like_words = 'lyrics'.split()
dislike_words = 'cover'.split()
clean_ends = lambda s: s.strip(' \t-+"\'=!.')


def search(s, verbose=False):
    param = urlencode({'q': 'site:youtube.com %s' % s})
    url = 'https://html.duckduckgo.com/html/?%s' % param
    body = subprocess.check_output('curl -k -H "user-agent: Mozilla/5.0" %s' % url, shell=True, stderr=subprocess.DEVNULL).decode()
    if verbose:
        print(body)
    artist = ''
    songs = []
    urls = set()
    names = set()
    hits = []
    for pagelink in pages.finditer(body):
        url = urldecode(pagelink.group(1).partition('%26')[0])
        name = html.unescape(pagelink.group(2))
        name = name.encode().partition(b'\xe2')[0].decode()
        name = tags.sub(' ', name)
        name = name.replace('~', ' - ').replace(':', ' - ').replace('"', ' ').replace('`', "'")
        name = ''.join((ch if ord(ch)<10000 else ' ') for ch in name)
        if verbose:
            print(name, url)
        if _match_words(url, bad_urls) or _match_words(name, bad_names):
            continue
        assert len(url) <= 60, 'url too long: '+url
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
    score = {h:len(h)*2 for h,u in hits}
    if verbose:
        print(score)
    # sort by no paranthesis
    score = {h:score[h]+h.find('(')+h.find('[') for h,u in hits}
    if verbose:
        print(score)
    # place those with dashes (-) first, assumed to be better named
    score = {h:score[h]+(h.index('-') if '-' in h else +50) for h,u in hits}
    if verbose:
        print(score)
    # place those with spaced dashes ( - ) first, assumed to be better named
    score = {h:score[h]+(h.index(' - ') if ' - ' in h else +50) for h,u in hits}
    if verbose:
        print(score)
    # sort by liked words
    score = {h:score[h]-75*len([1 for w in like_words if w in h.lower()]) for h,u in hits}
    if verbose:
        print(score)
    # sort by exact match, phrase by phrase + additional points for the correct order
    sl = s.lower()
    search_phrases = [p.strip() for p in sl.split('-')]
    def matchlen_pos(s1, s2, i1):
        i2 = s2.find(s1)
        score = 100
        if i2 >= 0:
            score = abs(i1-i2)
            # if verbose:
                # print(s1, s2, score)
        for w in dislike_words:
            if w in s2:
                score += 50
        return score
    score_phrase = lambda h: sum([matchlen_pos(p, h.lower(), sl.index(p)) for p in search_phrases])
    score = {h:score[h]+score_phrase(h) for h,u in hits}
    if verbose:
        print(score)
    hits = sorted(hits, key=lambda nu: score[nu[0]])
    if verbose:
        print('post score sort')
        print('\n'.join(str(h) for h in hits))
        print()
    # cleanup names
    for i,(name,url) in enumerate(hits):
        r = parenths.match(name)
        if r:
            words = [r.group(1), r.group(3)]
            inparenths = r.group(2).strip()
            if inparenths.lower() in sl:
                words += [inparenths]
            name = clean_ends(' '.join(w.strip() for w in words))
            hits[i][0] = name
    if verbose:
        print('post cleanup')
        print('\n'.join(str(h) for h in hits))
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
    if verbose:
        print('done')
        print(songs)
    # os._exit(1)
    return songs


def cache_song(url, wildcard):
    if 'youtube.com' in url:
        video = pafy.new(url)
        audiostream = max(video.audiostreams, key=lambda audio: abs(audio.rawbitrate-131072))
        fsize = audiostream.get_filesize()
        if fsize < 1e5 or fsize > 8e6:
            reason = 'small' if fsize < 1e6 else 'big'
            print('File too %s (%s B), refusing to download!' % (reason, fsize))
            return ''
        audiostream.download()
        src_filename = audiostream.filename
        base,ext = os.path.splitext(src_filename)
        dst_filename = wildcard.replace('.*', ext)
        os.rename(src_filename, dst_filename)
        return dst_filename


def _match_words(s, words):
    return any((word in s.lower()) for word in words)


if __name__ == '__main__':
    songs = search('Blind Guardian - Bright Eyes', verbose=True)
    # songs = search('Darin - Tvillingen', verbose=True)
    # songs = search('Victor Crone - Yes, I Will Wait', verbose=True)
    # songs = search('Miss Li - Komplicerad', verbose=True)
    # songs = search('Gym Class Heroes - Stereo Hearts', verbose=True)
    # songs = search('Oskar Linnros - Plåster', verbose=True)
    # songs = search('Liquido - Swing It', verbose=True)
    #cache_song(songs[0].uri, './something.*')
