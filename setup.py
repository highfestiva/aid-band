#!/usr/bin/env python3

from distutils.core import setup
import glob
import py2exe

setup(console=['aidband.py'],
	data_files=\
		[('', glob.glob('*.txt'))] +
		[(p, '') for p in glob.glob('cache_*')],
	)
