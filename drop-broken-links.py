#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''Throws away URLs of songs which are not cached.'''

from absong import ABSong
from codecs import open
from glob import glob
import os
import util


outp = []
songs = []
ok = flawed = 0
for line in open('favorites.txt', 'r', 'utf-8'):
    try:
        song = ABSong(line)
        wildcard = util._cachewildcard(song)
        if not glob(wildcard):
            print('-', song, song.uri, wildcard)
            outp.append('%s ~ %s ~' % (song.artist, song.name))
            flawed += 1
        else:
            outp.append('%s ~ %s ~ %s' % (song.artist, song.name, song.uri or ''))
            ok += 1
    except Exception as e:
        outp.append(line.strip())

print('%i%% flawed URIs dropped' % (100*flawed/(ok+flawed)))
open('favorites.txt', 'w', 'utf-8').write('\n'.join(outp))
