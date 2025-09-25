#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
from glob import glob
import os
import re
import requests
import subprocess


user_agent = 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
accept = 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
accept_encoding = 'Accept-Encoding: gzip, deflate, br, zstd'
accept_language = 'Accept-Language: en,en-US;q=0.9,sv;q=0.8'
referrer = 'Referer: https://search.brave.com/'
pages = re.compile(r'title:"(.*?)",url:"(https://.*?youtube.com/watch.+?)"')
parenths = re.compile(r'(.*?)\((.*?)\)(.*)')
bad_urls = 'list= /channel/'.split()
bad_names = 'review reaction'.split()
drop_words = 'album official video music youtube https'.split()
like_words = 'lyrics'.split()
dislike_words = 'cover'.split()
clean_ends = lambda s: s.strip(' \t-+"\'=!.')


def clean_hit(name, url, names, urls, verbose=False):
    if ' ' in url or ',' in url:
        return None, None
    name = name.replace('~', ' - ').replace(':', ' - ').replace('"', ' ').replace('`', "'")
    name = ''.join((ch if ord(ch)<10000 else ' ') for ch in name)
    if verbose:
        print(name, url)
    if _match_words(url, bad_urls) or _match_words(name, bad_names):
        return None, None
    assert len(url) <= 60, 'url too long: '+url
    words = [w for w in name.split() if not [b for b in drop_words if b in w.lower()]]
    name = ' '.join(words).strip()
    name = clean_ends(name)
    if not name:
        return None, None
    exists = (url in urls or name in names)
    urls.add(url)
    names.add(name)
    if exists:
        return None, None
    return name, url


def brave_hits(s, verbose=False):
    from urllib.parse import urlencode
    param = urlencode({'q': 'site:youtube.com %s' % s})
    url = f'https://search.brave.com/search?{param}'
    if verbose:
        print(url)
    body = subprocess.check_output(f'curl -k -H "{user_agent}" -H "{accept}" -H "{accept_encoding}" -H "{accept_language}" {url}', shell=True, stderr=subprocess.DEVNULL)
    if verbose:
        print(body)
    body = body.decode()
    urls = set()
    names = set()
    hits = []
    for pagelink in pages.finditer(body):
        name = pagelink.group(1)
        url,_,_ = pagelink.group(2).partition('&')
        name, url = clean_hit(name, url, names, urls, verbose=verbose)
        if not name:
            continue
        hits.append([name,url])
    return hits


def google_hits(s, verbose=False):
    from googlesearch import search as gsearch
    urls = set()
    names = set()
    hits = []
    for hit in gsearch('site:youtube.com ' + s, advanced=True):
        name, url = clean_hit(hit.title, hit.url, names, urls, verbose=verbose)
        if not name:
            continue
        hits.append([name,url])
    return hits


def google_cse_hits(s, verbose=False):
    from googleapiclient.discovery import build
    api_key = open('.google-api.key', 'rt').read().strip()
    cse_id = open('.google-cse.key', 'rt').read().strip()
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=s, cx=cse_id).execute()
    urls = set()
    names = set()
    hits = []
    if verbose:
        import pprint
        pprint.pprint(res)
    for hit in res['items']:
        name = hit['title']
        url = hit['formattedUrl']
        if 'youtu' not in url:
            continue
        name, url = clean_hit(name, url, names, urls, verbose=verbose)
        if not name:
            continue
        hits.append([name,url])
    return hits


def langsearch_hits(s, verbose=False):
    url = 'https://api.langsearch.com/v1/web-search'
    auth = open('.langsearch.key', 'rt').read().strip()
    json_data = {'query': f'List youtube videos of: {s}', 'summary': False}
    if verbose:
        print(url, 'POST', json_data)
    r = requests.post(url, headers={'Authorization': auth, 'Accept': 'application/json'}, json=json_data).json()
    urls = set()
    names = set()
    hits = []
    if verbose:
        import pprint
        pprint.pprint(r)
    for hit in r['data']['webPages']['value']:
        name = hit['name']
        url = hit['url']
        if 'youtu' not in url:
            continue
        name, url = clean_hit(name, url, names, urls, verbose=verbose)
        if not name:
            continue
        hits.append([name,url])
    return hits


def search(s, verbose=False):
    # hits = brave_hits(s, verbose=verbose)
    # hits = google_hits(s, verbose=verbose)
    hits = google_cse_hits(s, verbose=verbose)
    # hits = langsearch_hits(s, verbose=verbose)
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

    artist = ''
    songs = []
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


def cache_song_with_pafy(url, wildcard):
    if 'youtu' in url:
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


def cache_song(url, wildcard, verbose=True):
    if 'youtu' not in url:
        return
    cmd = f'yt-dlp -x "{url}"'
    body = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
    if verbose:
        print(body)
    src_filename = None
    _,_,yid = url.partition('?v=')
    yid,_,_ = yid.partition('&')
    for src_filename in glob(f'*{yid}*'):
        # if verbose:
        #     print(f'found file {src_filename}')
        break
    if not src_filename:
        print(f'ERROR: no file containing {yid} were downloaded')
        return
    if verbose:
        print(f'downloaded {src_filename}')
    _,ext = os.path.splitext(src_filename)
    dst_filename = wildcard.replace('.*', ext)
    os.rename(src_filename, dst_filename)
    return dst_filename


def _match_words(s, words):
    return any((word in s.lower()) for word in words)


if __name__ == '__main__':
    # songs = search('Blind Guardian - Bright Eyes', verbose=True)
    # songs = search('Darin - Tvillingen', verbose=True)
    # songs = search('Victor Crone - Yes, I Will Wait', verbose=True)
    # songs = search('Miss Li - Komplicerad', verbose=True)
    # songs = search('Gym Class Heroes - Stereo Hearts', verbose=True)
    # songs = search('Oskar Linnros - Plåster', verbose=True)
    # songs = search('Liquido - Swing It', verbose=True)
    # songs = search('Mr. Probz - Waves', verbose=True)
    #cache_song(songs[0].uri, './something.*')
    #songs = search('Fine Young Canibals - She Drives Me Crazy', verbose=True)
    # cache_song(songs[0].uri, './something.*', verbose=True)
    while True:
        term = input('enter artist - song: ')
        songs = search(term, verbose=True)
        for song in songs:
            print(song)
