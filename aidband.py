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
from killable import kill_self, single_threaded
import netpeeker
import os
import random
import re
import sr_radio
import speech
import subprocess
import sys
import threading
import time
from toplist import ilikeradio as load_pop_songs
import traceback
import util
import vorbis_encoder
import youtube_playlist
import youtube_radio


cmd = ''
stopped = True
proc = None
start_play_time = time.time()
active_url = ''
muzaks = None
allowcache = True
useshuffle = True
onrepeat = False
listname = None
playlist = []
playqueue = []
playing_callbacks = []
shuffleidx = []
ishits = False
playidx = 0
datadir = '.'
mplayer = ('mplayer.exe' if os.path.exists('mplayer.exe') else '') if 'win' in sys.platform.lower() else 'mpv'
mplayer_volume = '-volume' if 'win' in sys.platform.lower() else '--volume'
last_yt_search = 0
timer_stop_t = None
popen_kwargs = {}


@single_threaded
def stop():
    global proc,active_url,stopped
    if proc:
        try:
            proc.kill()
            proc.wait()
        except Exception as e:
            print(e)
        proc = None
        try:
            subprocess.check_output(['killall', mplayer], shell=True, stderr=subprocess.STDOUT)
        except:
            pass
    elif muzaks:
        muzaks.stop()
    active_url = ''
    stopped = True

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

@single_threaded
def play_url(url, cachewildcard):
    global proc,start_play_time,active_url,options,stopped
    start_play_time = time.time()+2 # cut some slack
    ok = False
    stop()
    spotify_init()
    if cachewildcard and allowcache: 
        fns = glob(cachewildcard)
        cachename = fns[0] if fns else None
        did_download = False
        if not cachename:
            if options.offline > 0:
                options.offline -= 1
                return False
            foreground = ishits or options.foreground_download
            if not foreground:
                song = playqueue[shuffleidx[playidx]]
                background_thread = threading.Thread(target=partial(bkg_save_song, song, cachewildcard))
                background_thread.start()
                return False
            cachename = youtube_radio.cache_song(url, cachewildcard)
            did_download = True
        if mplayer and cachename:
            if not options.only_cache:
                cmd = [mplayer, mplayer_volume, options.volume, cachename]
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **popen_kwargs)
            url = cachename
            ok = True
            if did_download:
                add_song()
    if not proc:
        if url.startswith('spotify') and not options.only_cache:
            if muzaks:
                muzaks.playsong(url)
                ok = True
            else:
                output("Won't play over spotify.")
        elif mplayer and url:
            if not options.only_cache:
                cmd = [mplayer, mplayer_volume, options.volume, _confixs(url)]
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **popen_kwargs)
            ok = True
        elif url:
            print('Get me %s!' % mplayer)
    start_play_time = time.time() # set again if process start took some time
    active_url = url if url else cachewildcard
    stopped = not ok
    return ok

def remove_from_cache(song):
    wc = util._cachewildcard(song)
    for fn in glob(wc):
        os.remove(fn)

def do_play_idx():
    global playqueue,options
    if playidx < len(playqueue):
        song = playqueue[shuffleidx[playidx]]
        for pc in playing_callbacks:
            pc(song)
        wildcard = ''
        if 'radio' not in listname:
            wildcard = util._cachewildcard(song)
            # if not os.path.exists(wildcard):
                # return
        if not glob(wildcard):
            update_url()
        output(song.artist, '-', song.name, '-', song.uri, '-', _confixs(wildcard))
        if play_url(song.uri, wildcard):
            return True

def play_idx(error_step=+1):
    global playqueue,playidx,stopped
    for _ in range(20):
        try:
            if do_play_idx():
                return True
        except Exception as e:
            output('play_idx cmd "%s" crash: %s' % (cmd, str(e)))
            time.sleep(1)
        playidx += error_step
        if playidx < 0:
            playidx = len(playqueue)-1
        if playidx >= len(playqueue):
            playidx = 0
    output('Unable to play anything, stopping playback')

def poll():
    if active_url.startswith('spotify'):
        if not muzaks or not muzaks.isplaying():
            try_next_song()
        return

    if not proc and not active_url:
        return
    if proc and proc.poll() == None:
        return
    if time.time()-start_play_time < 0.5: # gotta cut it some slack
        return
    try_next_song()

def raw_play_list(name, doplay=True):
    global listname,playlist,playqueue,playidx,shuffleidx,ishits,options
    listname = name
    doshuffle = useshuffle
    if listname == hotoptions.Hit:
        ishits = True
        playlist = [ABSong(s['name'], s['artists'][0]['name'], s['uri']) for s in load_pop_songs()]
        playqueue = playlist[:]
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
    return _match_ratio(song.searchname, search)

def match_artist(search, song):
    return _match_ratio(song.searchartist, search)

def split_artist_song(search, artist):
    wss = search.split()
    songwords = []
    artistwords = []
    for ws in wss:
        for wa in artist.split():
            if _match_ratio(ws, wa) >= 0.75:
                artistwords.append(ws)
                break
        else:
            songwords.append(ws)
    return ' '.join(artistwords), ' '.join(songwords)

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
            similar.append(song)
        if artist_perc >= 0.5:
            artist_similar.append(song)
    score = 0
    song_score = 0
    artist_score = 0
    if similar:
        score_songs = sorted(((match(search, s),s) for s in similar), key=lambda e:e[0], reverse=True)
        score = score_songs[0][0]
        score_songs = [(m,s) for m,s in score_songs if m > score*0.8]
        similar = [s for m,s in score_songs]
        song_scores = []
        artist_scores = []
        for search_artist in set(s.searchartist for s in similar):
            artistsearch,songsearch = split_artist_song(search, search_artist)
            if songsearch:
                song_scores.extend([match_song(songsearch, s) for s in similar])
            if artistsearch:
                artist_scores.extend([match_artist(artistsearch, s) for s in similar])
        song_score = max(song_scores) if song_scores else 0
        artist_score = max(artist_scores) if artist_scores else 0
    print('precise:', score, song_score, artist_score, util.str2prt(str(similar)))
    return score,song_score,artist_score,similar,artist_similar

def search_queue(search):
    search = search.lower()
    _,_,_,similar,artist_similar = search_precise(search)
    if not similar:
        similar = [song for song in playqueue if match(search, song) > 0.6]
    return sorted(similar, key=partial(match, search), reverse=True)

def songs_eq(s1, s2):
    ma = _match_ratio(s1.searchartist, s2.searchartist)
    ms = _match_ratio(s1.searchname, s2.searchname)
    return ma > 0.85 and ms > 0.75

def unique_songs(search, found_songs, songs):
    new_songs = []
    for fs in found_songs:
        for s in songs+new_songs:
            if songs_eq(s, fs):
                break
        else:
            new_songs += [fs]
    if ' - ' in search:
        new_songs = new_songs[:1]
    print('new songs found:', new_songs)
    return new_songs

def search_music(search):
    spotify_init()
    #return sorted(muzaks.search(search, type=Client.ARTISTS), key=lambda a: _match_ratio(a.name, search), reverse=True)
    songs = muzaks.search(search) if muzaks else []
    if not songs:
        inet_search = False
        score,song_score,artist_score,songs,artist_songs = search_precise(search)
        if song_score > 0.8: # "exact" match of a song
            pass
        elif 0 < song_score < 0.6 and artist_score > 0.8: # we don't have this particular song
            inet_search = True
        elif score < 0.51: # we don't have this song/artist/combo
            inet_search = True
        elif 1 <= len(artist_songs) <= 10:
            inet_search = True # we want more songs from this artist
        if inet_search:
            output('Searching Youtube for %s...' % search)
            found_songs = threshold_search(search)
            new_songs = unique_songs(search, found_songs, songs)
            songs += new_songs
    return songs

def play_search(search):
    global timer_stop_t
    timer_stop_t = None
    if 'radio' in listname:
        songs = sr_radio.search(search)
    else:
        if search != search.strip('@') or on_realtime_playlist():
            search = search.strip('@')
            songs = search_queue(search)
            if songs:
                requeue_songs(songs)
                return
        else:
            songs = search_music(search)
    if not songs:
        avoutput('Nothing found, try again.')
    queue_songs(songs)

def threshold_search_secs_left():
    min_delay = 11 # google will block us if we search too frequently
    delay = time.time() - last_yt_search
    return min_delay - delay

def threshold_search(search):
    t = threshold_search_secs_left()
    if t > 0:
        time.sleep(t)
    global last_yt_search
    last_yt_search = time.time()
    return youtube_radio.search(search)

def bkg_save_song(song, cachewildcard):
    global playlist
    youtube_radio.cache_song(song.uri, cachewildcard)
    if song not in playlist:
        playlist += [song]
        save_list(playlist)

def ext_add_to_favorites():
    '''Add+save song to favorites.'''
    song = playqueue[shuffleidx[playidx]]
    fn = os.path.join(datadir, hotoptions.Favorites+'.txt')
    f = codecs.open(fn, 'a', 'utf-8')
    f.write('%s ~ %s ~ %s\n' % (song.artist, song.name, song.uri or ''))


def add_song():
    global playlist,playqueue
    if shuffleidx[playidx:playidx+1]:
        song = playqueue[shuffleidx[playidx]]
        if on_realtime_playlist():
            ext_add_to_favorites()
            avoutput('Hit %s added to %s.' % (song.name, hotoptions.Favorites))
            return
        if song not in playlist:
            playlist += [song]
            save_list(playlist)
            if options.verbose:
                avoutput('%s added to %s.' % (song.name,_simple_listname()))
            return True
        else:
            if options.verbose:
                avoutput('%s already in %s.' % (song.name,_simple_listname()))
    else:
        if options.verbose:
            avoutput('Play queue is empty, no song to add.')
    _validate()

def drop_song():
    global playlist,playqueue,shuffleidx
    if playidx < len(shuffleidx) and not on_realtime_playlist():
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

def try_next_song():
    global timer_stop_t
    if timer_stop_t and timer_stop_t < time.time():
        stop()
        timer_stop_t = None
        avoutput('Goodnight!')
        for pc in playing_callbacks:
            pc(None)
    else:
        next_song();

def step_song(step):
    global playidx
    if not onrepeat:
        playidx += step
    play_idx(error_step=step)

def toggle_shuffle():
    global useshuffle,playidx,shuffleidx
    useshuffle = not useshuffle
    curidx = shuffleidx[playidx]
    shuffleidx = list(range(len(playqueue)))
    if useshuffle:
        random.shuffle(shuffleidx)
    playidx = shuffleidx.index(curidx)
    avoutput('Shuffle.' if useshuffle else 'Playing in order.')
    _validate()
    return useshuffle

def run_command(cmd):
    if cmd.startswith('!'):
        cmd = cmd[1:].strip()
    if cmd.startswith('volume'):
        options.volume = cmd.partition(' ')[2]
        avoutput('Volume set to %s.' % options.volume)
    elif cmd.startswith('timer'):
        global timer_stop_t
        minutes = float(cmd.partition(' ')[2])
        timer_stop_t = minutes * 60 + time.time()
        avoutput('Timer set to %s minutes.' % minutes)
    else:
        run_ext_cmd(cmd.lstrip('!'))

def update_url():
    global playqueue,playidx,playlist,options,stopped
    if playidx >= len(playqueue) or options.offline > 0:
        return False
    song = playqueue[shuffleidx[playidx]]
    if not song.uri or ('spotify:' in song.uri and not options.dont_replace_spotify):
        foreground = ishits or options.foreground_download
        if threshold_search_secs_left()>0 and not foreground:
            # can't search right away, so instead skip ahead to a playable song
            time.sleep(0.1) # don't burn all cpu for nothin'
            return False
        search = song.artist + ' - ' + song.name
        songs = threshold_search(search)
        if songs:
            song.uri = songs[0].uri
            save_list(playlist)
            return True
        else:
            avoutput('No results on Youtube; are we blocked by Google?')
            options.offline = 3
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
    if len(songs) == 1 and not useshuffle and songs[0] in playqueue:
        return requeue_songs(songs)
    newidx = list(range(len(playqueue),len(playqueue)+len(songs)))
    playqueue += songs
    shuffleidx = shuffleidx[:playidx+1] + newidx + shuffleidx[playidx+1:]
    _validate()
    next_song()

def requeue_songs(songs):
    '''Repositions songs to end up next in the play queue'''
    global playidx, playqueue, shuffleidx
    songs = list(songs)
    if not songs:
        return
    if len(songs) == 1 and not useshuffle:
        # move "song pointer" to that position
        pq_idx = playqueue.index(songs[0])
        playidx = pq_idx-1 if pq_idx > 0 else len(playqueue)-1
    else:
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

def on_realtime_playlist():
    return ishits or listname.startswith('pl_')

def load_list():
    songs = []
    fn = os.path.join(datadir,listname+'.txt')
    if not os.path.exists(fn):
        return songs
    if on_realtime_playlist():
        try:
            pl_url = open(fn).read().strip()
            for artist,songname,url in youtube_playlist.playlist(pl_url):
                songs += [ABSong(songname,artist,url)]
        except:
            pass
    else:
        for line in codecs.open(fn, 'r', 'utf-8'):
            try:
                songs += [ABSong(line)]
            except:
                pass
    return songs

def save_list(songlist):
    if on_realtime_playlist():
        return
    fn = os.path.join(datadir,listname+'.txt')
    f = codecs.open(fn, 'w', 'utf-8')
    f.write('Playlist for AidBand. Each line contains artist, song name and URL. The first two can be left empty if file:// and otherwise the URL may be left empty if varying.\n')
    for song in songlist:
        f.write('%s ~ %s ~ %s\n' % (song.artist, song.name, song.uri or ''))

def output(*args):
    s = util.str2prt(*args)
    print(s)
    netpeeker.output(s)

def avoutput(*args):
    s = ' '.join([str(a) for a in args])
    output(s)
    speech.say(s)

def run_ext_cmd(cmd):
    cmd = cmd.split()
    cmd,args = cmd[0],cmd[1:]
    try:
        exec(open('ext/'+cmd.strip()).read(), {'args':args})
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

def _confixs(s):
    return util.str2prt(s)

def _match_ratio(s1,s2):
    return difflib.SequenceMatcher(None,s1,s2).ratio()


parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', dest='datadir', metavar='DIR', default='.', help="directory containing playlists and cache (default is '.')")
parser.add_argument('--with-spotify', action='store_true', default=False, help="don't login to music service, meaning only radio can be played")
parser.add_argument('--dont-replace-spotify', action='store_true', default=False, help="don't replace spotify URI's with youtube ones")
parser.add_argument('--only-cache', action='store_true', default=False, help="don't play any music, just download the files")
parser.add_argument('--foreground-download', action='store_true', default=False, help="wait for file to finish downloading instead of skipping ahead")
parser.add_argument('--offline', action='store_true', default=False, help='only play from disk cache')
parser.add_argument('--webserve', action='store_true', default=False, help='serve html playing')
parser.add_argument('--volume', help='pass volume to mplayer, alt. use $CON_VOLUME')
parser.add_argument('--no-remote-control', action='store_true', help='skip listening to tcp port for remote connects')
parser.add_argument('--bg-convert-wav', action='store_true', help='convert .wav to .ogg in the background')
parser.add_argument('-v', '--verbose', action='store_true')
options = parser.parse_args()
options.nosp = not options.with_spotify
options.offline = 1e8 if options.offline else 0
if not options.volume:
    if 'CON_VOLUME' in os.environ:
        options.volume = os.environ['CON_VOLUME']
    else:
        options.volume = '100'
if options.no_remote_control:
    class Dummy:
        def dummy(self, *args, **kwargs):
            return ''
        def __getattr__(self, _):
            return self.dummy
    netpeeker = Dummy()
if options.verbose:
    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger('urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

datadir = options.datadir
try: os.mkdir(os.path.join(datadir,'cache'))
except: pass

if __name__ == '__main__':
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
    if options.webserve:
        import htmlserver
        htmlserver.run_threaded()
    raw_play_list(hotoptions.Favorites, doplay=False)
    if options.bg_convert_wav:
        vorbis_encoder.async_maintain_cache_dir('cache')

    while True:
        try:
            time.sleep(0.2)    # Let CPU rest in case of infinite loop bug.
            output('Enter search term:')
            cmd = ''
            while not cmd:
                event.wait(2)
                event.clear()
                time.sleep(0.2)    # Let CPU rest in case of infinite loop bug.
                if not stopped:
                    poll()
                cmd = keypeeker.peekstr() + netpeeker.peekstr()
            if options.verbose:
                print('running cmd:', cmd)
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
                if not stopped:
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
            elif cmd == '+':
                add_song()
            elif cmd == '-':
                onrepeat = False
                drop_song()
            elif cmd == '<Left>':
                onrepeat = False
                prev_song()
            elif cmd == '<Right>':
                onrepeat = False
                next_song()
            elif cmd == '<Up>': # toggle repeat
                onrepeat = not onrepeat
                avoutput('Repeat.' if onrepeat else 'Playing in sequence.')
            elif cmd == '\t': # toggle shuffle
                onrepeat = False
                toggle_shuffle()
            elif cmd.startswith('!'):
                run_command(cmd)
            elif cmd.endswith('\r'):
                onrepeat = False
                cmd = cmd.strip()
                if len(cmd) < 2:
                    output('Too short search string "%s".' % cmd)
                    continue
                output(cmd)
                if ':' not in cmd:
                    play_search(cmd)
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
