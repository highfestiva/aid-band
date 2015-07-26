#!/usr/bin/env python3

from distutils.core import setup
import py2exe

py2exe_options = { 'optimize': 2 }
setup(console=['fill_spotify_playlists.py'], options = {'py2exe': py2exe_options})
