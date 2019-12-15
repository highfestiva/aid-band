#!/usr/bin/env python3

from glob import glob
import os
from os.path import exists
import subprocess
from time import sleep
from threading import Thread

_quit = False

def _find_ffmpeg():
    files = glob('c:/Program Files*/ffmpeg*/bin/ffmpeg.exe') + glob('/usr/bin/avconv') + glob('/usr/bin/ffmpeg')
    if files:
        f,oargs = files[-1],[]
        if 'avconv' in f:
            oargs += ['-acodec', 'libvorbis']
        return f,oargs
    return None,None

ffmpeg,oargs = _find_ffmpeg()

def vorbis_encode(fn):
    if not ffmpeg:
        print('Vorbis compression installed. Install libav-tools or ffmpeg!')
        return
    oggfn = fn.replace('.wav','.ogg')
    if exists(oggfn):
        os.remove(oggfn)    # Possibly half-made version.
    cmd = [ffmpeg, '-i', fn] + oargs + [oggfn]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.wait() == 0:
        if exists(oggfn):
            print('%s -> %s went fine.' % (fn, oggfn))
            os.remove(fn)
    else:
        print('Error when converting %s to Vorbis!' % fn)

def maintain_cache_dir(dirname):
    try:
        for w in glob(dirname+'/*.wavy'):    # Unfinished business.
            os.remove(w)
    except:
        pass
    while not _quit:
        try:
            for w in glob(dirname+'/*.wav'):
                vorbis_encode(w)
        except Exception as e:
            print('Crashed while trying to Vorbis encode:', e)
        for _ in range(30):
            if _quit:
                break
            sleep(1)

def async_maintain_cache_dir(dirname):
    t = Thread(target=maintain_cache_dir, args=(dirname,))
    t.daemon = True
    t.start()

def quit():
    global _quit
    _quit = True

if __name__ == '__main__':
    async_maintain_cache_dir('cache')
    quit()
