#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from absong import ABSong
import argparse
import codecs
import difflib
from functools import partial
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
import util
import vorbis_encoder
import youtube_radio


proc = None
start_play_time = time.time()
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
    global proc,active_url
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

def play_url(url, cachewildcard):
    ok = False
    stop()
    spotify_init()
    global proc,start_play_time,active_url,options
    if cachewildcard and allowcache: 
        fns = glob(cachewildcard)
        cachename = fns[0] if fns else None
        did_download = False
        if not cachename:
            cachename = youtube_radio.cache_song(url, cachewildcard)
            did_download = True
        if mplayer and cachename:
            if not options.only_cache:
                cmd = [mplayer, '-volume', options.volume, cachename]
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            url = cachename
            ok = True
            if did_download:
                add_song(verbose=False)
    if not proc:
        if url.startswith('spotify') and not options.only_cache:
            if muzaks:
                muzaks.playsong(url)
                ok = True
            else:
                output("Won't play over spotify.")
        elif mplayer and url:
            if not options.only_cache:
                cmd = [mplayer, '-volume', options.volume, _confixs(url)]
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok = True
        elif url:
            print('Get me mplayer!')
    start_play_time = time.time()
    active_url = url if url else cachewildcard
    return ok

def remove_from_cache(song):
    wc = _cachewildcard(song)
    for fn in glob(wc):
        os.remove(fn)

def do_play_idx():
    global playqueue,options
    if playidx < len(playqueue):
        song = playqueue[shuffleidx[playidx]]
        wildcard = ''
        if 'radio' not in listname:
            wildcard = _cachewildcard(song)
            # if not os.path.exists(wildcard):
                # return
        if not glob(wildcard):
            update_url()
        output(song.artist, '-', song.name, '-', song.uri, '-', _confixs(wildcard))
        if play_url(song.uri, wildcard):
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

def match(search, song):
    s = song
    return max([_match_ratio(t,search) for t in (s.searchartist, s.searchname, s.searchname+' '+s.searchartist, s.searchartist+' '+s.searchname)])

def match_song(search, song):
    '''Exclude *exclusively* artist'''
    s = song
    return max([_match_ratio(t,search) for t in (s.searchname, s.searchname+' '+s.searchartist, s.searchartist+' '+s.searchname)])

def search_precise(search):
    search = search.lower()
    search_words = [util.rawstr(s) for s in search.split()]
    similar = []
    artist_similar = []
    for song in playqueue:
        awords = song.searchartist.split()
        artist_perc = sum(min(1.5,len(sword)/4) for sword in search_words if sword in awords) / len(search_words)
        nwords = song.searchname.split()
        name_perc = sum(min(1.5,len(sword)/4) for sword in search_words if sword in nwords) / len(search_words)
        if artist_perc+name_perc >= 0.5:
            # print('precise match for:', str(song).encode(), artist_perc, name_perc)
            similar.append(song)
        if artist_perc >= 0.5:
            artist_similar.append(song)
    score = 0
    song_score = 0
    if similar:
        o_similar = similar
        score_songs = sorted(((match(search, s),s) for s in similar), key=lambda e:e[0], reverse=True)
        score = score_songs[0][0]
        score_songs = [(m,s) for m,s in score_songs if m > score*0.8]
        similar = [s for m,s in score_songs]
        song_score = max([match_song(search, s) for s in o_similar])
    print('precise:', score, str(str(similar).encode())[2:-1])
    return score,song_score,similar,artist_similar

def search_queue(search):
    search = search.lower()
    score,song_score,similar,artist_similar = search_precise(search)
    if not similar:
        similar = [song for song in playqueue if match(search, song) > 0.6]
    return sorted(similar, key=partial(match, search), reverse=True)

def songs_eq(s1, s2):
    m = match(s1.searchartist + ' ' + s1.searchname, s2)
    # print('"%s" "%s" == "%s" "%s" -> %f' % (s1.searchname, s1.searchartist, s2.searchname, s2.searchartist, m))
    return m > 0.7

def drop_existing(found_songs, songs):
    new_songs = []
    for fs in found_songs:
        for s in songs:
            if songs_eq(s, fs):
                break
        else:
            new_songs += [fs]
    print('new songs found:', new_songs)
    return new_songs

def search_music(search):
    spotify_init()
    #return sorted(muzaks.search(search, type=Client.ARTISTS), key=lambda a: _match_ratio(a.name, search), reverse=True)
    songs = muzaks.search(search) if muzaks else []
    if not songs:
        score,song_score,songs,artist_songs = search_precise(search)
        if song_score > 0.8:
            pass # YOU PLAY NOW!
        elif score < 0.51 or 1 <= len(artist_songs) <= 10:
            output('Searching Youtube for %s...' % search)
            found_songs = youtube_radio.search(search)
            new_songs = drop_existing(found_songs, songs)
            songs = new_songs + songs
    return songs

def play_search(search):
    if 'radio' in listname:
        songs = sr_radio.search(search)
    else:
        if search != search.strip('@'):
            search = search.strip('@')
            songs = search_queue(search)
            if songs:
                requeue_songs(songs)
        else:
            songs = search_music(search)
    if not songs:
        avoutput('Nothing found, try again.')
    queue_songs(songs)

def add_song(verbose=True):
    global playlist,playqueue
    if shuffleidx[playidx:playidx+1]:
        song = playqueue[shuffleidx[playidx]]
        if song not in playlist:
            playlist += [song]
            save_list(playlist)
            if verbose:
                avoutput('%s added to %s.' % (song.name,_simple_listname()))
            return True
        else:
            if verbose:
                avoutput('%s already in %s.' % (song.name,_simple_listname()))
    else:
        if verbose:
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
    step_song(-1)

def next_song():
    step_song(+1)

def step_song(step):
    global playqueue,playidx
    for _ in range(3): # make up to three attempts
        playidx += step
        if playidx < 0:
            playidx = len(playqueue)-1
        if playidx >= len(playqueue):
            playidx = 0
        try:
            play_idx()
            break
        except Exception as e:
            output('step_song "%s" crash: %s' % (cmd, str(e)))

def update_url():
    global playqueue,playidx,playlist,options,stopped
    if playidx >= len(playqueue):
        return False
    song = playqueue[shuffleidx[playidx]]
    if not song.uri or ('spotify:' in song.uri and not options.dont_replace_spotify):
        search = song.artist + ' - ' + song.name
        songs = youtube_radio.search(search)
        if songs:
            song.uri = songs[0].uri
            save_list(playlist)
            return True
        else:
            avoutput('No results on Youtube; are we blocked by Google?')
            stopped = True
            stop()
            assert False
    elif not song.uri:
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

def requeue_songs(songs):
    '''Repositions songs to end up next in the play queue'''
    songs = list(songs)
    if not songs:
        return
    global playidx, playqueue, shuffleidx
    in_idx = playidx + 1
    for song in songs:
        pq_idx = playqueue.index(song)
        sh_idx = shuffleidx.index(pq_idx)
        shuffleidx = shuffleidx[:sh_idx] + shuffleidx[sh_idx+1:] # drop from current pos
        if sh_idx < in_idx:
            in_idx -= 1
        if sh_idx <= playidx: # back up current playing index, as we've effectivly dropped one song earlier in the list
            playidx -= 1
        shuffleidx = shuffleidx[:in_idx] + [pq_idx] + shuffleidx[in_idx:] # insert in next slot
        in_idx += 1 # insert next song beyond
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

def run_ext_cmd(cmd):
    try:
        exec(open('ext/'+cmd.strip()).read())
    except Exception as e:
        output('ext_cmd "%s" crash: %s' % (cmd, str(e)))

def _validate():
    if not ishits:
        assert len(playqueue) >= len(playlist)
    assert len(playqueue) == len(shuffleidx)
    for i in range(len(playqueue)):
        assert shuffleidx[i] < len(playqueue)
    assert playidx < len(shuffleidx) or len(shuffleidx) == 0

def _simple_listname():
    return listname.split('_')[-1]

def _cachewildcard(song):
    s = str(song.artist) + '-' + song.name
    replacements = {'/':'_', '\\':'_', ':':'_', '?':'', '(':'', ')':'', '[':'', ']':''}
    for a,b in replacements.items():
        s = s.replace(a,b)
    s = os.path.join(datadir, 'cache/'+s+'.*')
    return s

def _confixs(s):
    if 'win' in sys.platform.lower():
        return ''.join(str(s).encode().decode('ascii', 'ignore').split('?'))
    return s

def _match_ratio(s1,s2):
    return difflib.SequenceMatcher(None,s1,s2).ratio()


parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', dest='datadir', metavar='DIR', default='.', help="directory containing playlists and cache (default is '.')")
parser.add_argument('--with-spotify', action='store_true', default=False, help="don't login to music service, meaning only radio can be played")
parser.add_argument('--dont-replace-spotify', action='store_true', default=False, help="don't replace spotify URI's with youtube ones")
parser.add_argument('--only-cache', action='store_true', default=False, help="don't play any music, just download the files")
parser.add_argument('--volume', default='100', help='pass volume to mplayer')
options = parser.parse_args()
options.nosp = not options.with_spotify

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
netpeeker.init(handle_login, handle_keys)
keypeeker.init(handle_keys)
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
        elif cmd.startswith('!'):
            cmd = cmd.strip()
            if cmd.startswith('!volume'):
                options.volume = cmd.partition(' ')[2]
                avoutput('Volume set to %s.' % options.volume)
            else:
                run_ext_cmd(cmd.lstrip('!'))
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
