#!/bin/bash

rm -Rf dist/
python3 -OO setup.py py2exe --bundle 1
#cp /c/Program\ Files\ \(x86\)/mplayer/mplayer.exe dist/
mv dist/aidband.exe dist/AidBand.exe
echo -n 'ABC' > dist/password
