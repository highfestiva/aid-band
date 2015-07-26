#!/usr/bin/env python3

from distutils.core import setup
import glob
import py2exe

py2exe_options = { 'includes': ['encodings.idna', 'pyttsx.drivers.sapi5', 'win32com.gen_py.C866CA3A-32F7-11D2-9602-00C04F8EE628x0x5x4'],
		   'typelibs': [('{C866CA3A-32F7-11D2-9602-00C04F8EE628}', 0, 5, 4)],
		   'optimize': 2 }

setup(console=['aidband.py'], data_files=[('',['AidBand.sh'])], options = {'py2exe': py2exe_options})
