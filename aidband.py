#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import argparse
import codecs
import difflib
from glob import glob
import hotoptions
import interruptor
import keypeeker
from killable import kill_self
import netpeeker
import os.path
import random
import re
import sr_radio
import speech
import subprocess
import sys
import threading
import time
import traceback
import vorbis_encoder


proc = None
start_play_time = time.time()
cache_write_name = None
active_url = ''
muzaks = None
allowcache = True
useshuffle = True
listname = None
playlist = []
playqueue = []
shuffleidx = []
ishits = False
playidx = 0
datadir = '.'
mplayer = ('mplayer.exe' if os.path.exists('mplayer.exe') else '') if 'win' in sys.platform.lower() else 'mplayer'


def stop():
    global proc,cache_write_name,active_url
    if proc:
        try:
            proc.kill()
            proc.wait()
        except Exception as e:
            print(e)
        proc = None
        try:
            subprocess.check_output('killall mplayer'.split(), shell=True, stderr=subprocess.STDOUT)
        except:
            pass
        if cache_write_name:
            import os
            try: os.remove(cache_write_name)
            except: pass
            cache_write_name = None
    elif muzaks:
        muzaks.stop()
    active_url = ''

def spotify_init():
    global options,muzaks
    try:
        if not muzaks and not options.nosp:
            username,password = open('sp_credentials','rt').read().split('~~~')
            from spotify import Client
            muzaks = Client(username,password)
    except Exception as e:
        print('Exception during spotify login:', e)
        print('Will play offline only.')
        options.nosp = True

def spotify_exit():
    global muzaks
    if muzaks:
        muzaks.quit()
    muzaks = None

def play_url(url, cachename):
    ok = False
    stop()
    spotify_init()
    global proc,start_play_time,cache_write_name,active_url
    cache_write_name = None
    if cachename and allowcache: 
        if not os.path.exists(cachename):
            fns = glob(cachename.replace('-','*-',1))
            if fns:
                cachename = fns[0]
        if mplayer and os.path.exists(cachename):
            cmd = [mplayer, cachename]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = cachename
            ok = True
    if not proc:
        if url.startswith('spotify'):
            if muzaks:
                muzaks.playsong(url)
                ok = True
            else:
                output("Won't play over spotify.")
        elif mplayer and url:
            cmd = [mplayer, _confixs(url)]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok = True
        elif url:
            print('Get me mplayer!')
    start_play_time = time.time()
    active_url = url if url else cachename
    return ok

def remove_from_cache(song):
    fn = _cachename(song)
    if os.path.exists(fn):
        os.remove(fn)

def do_play_idx():
    global playqueue
    if playidx < len(playqueue):
        song = playqueue[shuffleidx[playidx]]
        fn = ''
        if 'radio' not in listname:
            fn = _cachename(song)
            # if not os.path.exists(fn):
                # return
        if not song.uri:
            update_url()
        output(song.artist, '-', song.name, '-', song.uri, '-', _confixs(fn))
        if play_url(song.uri, fn):
            song = ABSong(song.name,song.artist,song.uri)
            playqueue[shuffleidx[playidx]] = song
            return True

def play_idx():
    return do_play_idx()

def poll():
    if active_url.startswith('spotify'):
        if not muzaks or not muzaks.isplaying():
            next_song()
        return

    if not proc and not active_url:
        return
    if proc and proc.poll() == None:
        return
    global cache_write_name
    if cache_write_name and os.path.exists(cache_write_name):
        cache_write_name = None
        play_idx()    # Play from cache.
    elif time.time()-start_play_time < 5.0:    # Stopped after short amount of time? URL probably fucked.
        if update_url():
            play_idx()
        else:
            next_song()
    else:
        next_song()

def raw_play_list(name, doplay=True):
    global listname
    listname = name
    global playlist,playqueue,playidx,shuffleidx,ishits
    doshuffle = useshuffle
    if listname == hotoptions.Hit:
        ishits = True
        playqueue = muzaks.popular()
        listname = hotoptions.Favorites
        playlist = load_list()
        doshuffle = False
    else:
        ishits = False
        playlist = load_list()
        playqueue = playlist[:]
        if 'radio' in listname:
            doshuffle = False
    shuffleidx = list(range(len(playqueue)))
    if doshuffle:
        random.shuffle(shuffleidx)
    playidx = 0
    _validate()
    if doplay:
        if playqueue:
            play_idx()
        else:
            stop()
    return playqueue

def play_list(name):
    pq = raw_play_list(name)
    if pq:
        avoutput(_simple_listname())
    else:
        avoutput('%s playlist is empty, nothing to play.' % _simple_listname())

def search_queue(search):
    match = lambda s: max([_match_ratio(t,search) for t in (s.searchartist, s.searchname, s.searchname+' '+s.searchartist, s.searchartist+' '+s.searchname)])
    similar = [song for song in playqueue if match(song) > 0.6]
    return sorted(similar, key=match, reverse=True)

def search_music(search):
    spotify_init()
    #return sorted(muzaks.search(search, type=Client.ARTISTS), key=lambda a: _match_ratio(a.name, search), reverse=True)
    songs = muzaks.search(search) if muzaks else []
    return songs if songs else search_queue(search)

def play_search(search):
    if 'radio' in listname:
        songs = sr_radio.search(search)
    else:
        if search != search.strip('@'):
            search = search.strip('@')
            songs = search_queue(search)
            # We can't queue these songs, they are already in playqueue.
            if songs:
                global playidx
                idx = playqueue.index(songs[0])
                playidx = shuffleidx.index(idx)
                play_idx()
                return
        songs = search_music(search)
    if not songs:
        avoutput('Nothing found, try again.')
    queue_songs(songs)

def add_song():
    global playlist,playqueue
    if shuffleidx[playidx:playidx+1]:
        song = playqueue[shuffleidx[playidx]]
        if song not in playlist:
            playlist += [song]
            save_list(playlist)
            avoutput('%s added to %s.' % (song.name,_simple_listname()))
            return True
        else:
            avoutput('%s already in %s.' % (song.name,_simple_listname()))
    else:
        avoutput('Play queue is empty, no song to add.')
    _validate()

def drop_song():
    global playlist,playqueue,shuffleidx
    if playidx < len(shuffleidx):
        pqidx = shuffleidx[playidx]
        song = playqueue[pqidx]
        playqueue = playqueue[:pqidx] + playqueue[pqidx+1:]
        shuffleidx = shuffleidx[:playidx] + shuffleidx[playidx+1:]
        shuffleidx = [s if s<pqidx else s-1 for s in shuffleidx]    # Reduce all above a certain index.
        playlist = list(filter(lambda s: s!=song, playlist))
        play_idx()
        save_list(playlist)
        remove_from_cache(song)
        avoutput('%s dropped from %s.' % (song.name,_simple_listname()))
        return True
    else:
        avoutput('Play queue is empty, no song to remove.')
    _validate()

def prev_song():
    global playqueue,playidx
    playidx -= 1
    if playidx < 0:
        playidx = len(playqueue)-1 if playqueue else 0
    play_idx()

def next_song():
    global playqueue,playidx
    playidx += 1
    if playidx >= len(playqueue):
        playidx = 0
    play_idx()

def update_url():
    global playqueue,playidx,playlist
    if playidx >= len(playqueue):
        return False
    song = playqueue[shuffleidx[playidx]]
    if not song.uri:
        spotify_init()
        search = '%s %s' % (song.name,song.artist)
        if muzaks:
            s = muzaks.search(search)
            if s:
                song.uri = s[0].uri
                save_list(playlist)
                return True
        return False

def execute(cmd):
    cmd,params = [c.strip() for c in cmd.split(':')]
    if cmd == 'say':
        speech.say(params)
    if cmd == 'pwr' and params == 'off':
        import win32api
        win32api.ExitWindowsEx(24,0)

def queue_songs(songs):
    songs = list(songs)
    if not songs:
        return
    global playqueue,playidx,shuffleidx
    newidx = list(range(len(playqueue),len(playqueue)+len(songs)))
    playqueue += songs
    shuffleidx = shuffleidx[:playidx+1] + newidx + shuffleidx[playidx+1:]
    _validate()
    next_song()

def load_list():
    songs = []
    fn = os.path.join(datadir,listname+'.txt')
    if not os.path.exists(fn):
        return songs
    for line in codecs.open(fn, 'r', 'utf-8'):
        try:
            artist,songname,url = [w.strip() for w in line.split('~')]
            songs += [ABSong(songname,artist,url)]
        except:
            pass
    return songs

def save_list(songlist):
    fn = os.path.join(datadir,listname+'.txt')
    f = codecs.open(fn, 'w', 'utf-8')
    f.write('Playlist for AidBand. Each line contains artist, song name and URL. The first two can be left empty if file:// and otherwise the URL may be left empty if varying.\n')
    for song in songlist:
        f.write('%s ~ %s ~ %s\n' % (song.artist, song.name, song.uri))

def output(*args):
    s = ' '.join([str(a) for a in args])
    try:
        if sys.platform == 'linux':
            print(s,end='\r\n')
        else:
            print(s.encode('cp850','ignore').decode('cp850'))
    except UnicodeEncodeError:
        print(s.encode('ascii','ignore').decode('ascii'))
    netpeeker.output(s)

def avoutput(*args):
    s = ' '.join([str(a) for a in args])
    output(s)
    speech.say(s)

def _validate():
    if not ishits:
        assert len(playqueue) >= len(playlist)
    assert len(playqueue) == len(shuffleidx)
    for i in range(len(playqueue)):
        assert shuffleidx[i] < len(playqueue)
    assert playidx < len(shuffleidx) or len(shuffleidx) == 0

def _simple_listname():
    return listname.split('_')[-1]

def _cachename(song):
    return os.path.join(datadir, 'cache/'+(str(song.artist)+'-'+song.name+'.ogg').replace('/','_').replace('\\','_').replace(':','_'))

def _confixs(s):
    if 'win' in sys.platform.lower():
        return ''.join(str(s).encode().decode('ascii', 'ignore').split('?'))
    return s

def _match_ratio(s1,s2):
    return difflib.SequenceMatcher(None,s1,s2).ratio()


parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', dest='datadir', metavar='DIR', default='.', help="directory containing playlists and cache (default is '.')")
parser.add_argument('--without-spotify', dest='nosp', action='store_true', default=False, help="don't login to music service, meaning only radio can be played")
options = parser.parse_args()

datadir = options.datadir
try: os.mkdir(os.path.join(datadir,'cache'))
except: pass

tid = threading.current_thread().ident
event = threading.Event()
def handle_login():
    output('Welcome to aid-band cmdline interface!')
    if stopped:
        output('No music currently playing.')
    else:
        song = playqueue[shuffleidx[playidx]]
        output('Currently playing "%s" by %s' % (song.name, song.artist))
def handle_keys(k):
    interruptor.handle_keys(tid,k)
    event.set()
keypeeker.init(handle_keys)
netpeeker.init(handle_login, handle_keys)
spotify_init()
raw_play_list(hotoptions.Favorites, doplay=False)
vorbis_encoder.async_maintain_cache_dir('cache')

stopped = True
while True:
    try:
        time.sleep(0.2)    # Let CPU rest in case of infinite loop bug.
        output('Enter search term:')
        cmd = ''
        while not cmd:
            event.wait(2)
            time.sleep(0.2)    # Let CPU rest in case of infinite loop bug.
            if not stopped:
                poll()
            cmd = keypeeker.peekstr() + netpeeker.peekstr()
        if cmd in ('<quit>','<softquit>'):
            vorbis_encoder.quit()
            stop()
            netpeeker.stop()
            keypeeker.stop()
            if muzaks: muzaks.quit()
            if cmd == '<softquit>':
                break
            kill_self()
        if cmd == '<F12>':
            stopped = not stopped
            if stopped:
                stop()
                spotify_exit()
                output('Audio stopped.')
            else:
                play_idx()
            continue
        fkeys = re.findall(r'<F(\d+)>',cmd)
        if fkeys:
            fkey_idx = int(fkeys[-1])-1
            if len(hotoptions.all) > fkey_idx:
                ln = hotoptions.all[fkey_idx]
                play_list(ln)
                stopped = False
        elif cmd == '+':
            add_song()
        elif cmd == '-':
            if drop_song():
                stopped = False
        elif cmd == '<Left>':
            prev_song()
            stopped = False
        elif cmd == '<Right>':
            next_song()
            stopped = False
        elif cmd == '\t':
            useshuffle = not useshuffle
            if shuffleidx:
                curidx = shuffleidx[playidx]
                shuffleidx = list(range(len(playqueue)))
                if useshuffle:
                    random.shuffle(shuffleidx)
                playidx = shuffleidx.index(curidx)
                avoutput('Shuffle.' if useshuffle else 'Playing in order.')
            _validate()
        elif cmd.endswith('\r'):
            cmd = cmd.strip()
            if len(cmd) < 2:
                output('Too short search string "%s".' % cmd)
                continue
            output(cmd)
            if ':' not in cmd:
                play_search(cmd)
                stopped = False
            else:
                execute(cmd)
    except Exception as e:
        try:
            traceback.print_exc()
            output(e)
            keypeeker.getstr()    # Clear keyboard.
            netpeeker.getstr()    # Clear remote keyboard.
        except Exception as e:
            print('FATAL ERROR!')
        time.sleep(1)
