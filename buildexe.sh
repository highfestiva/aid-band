#!/bin/bash

rm -Rf dist/ AidBand/ AidBand.tar.gz
python3 -OO setup.py py2exe --bundle 1
#cp /c/Program\ Files\ \(x86\)/mplayer/mplayer.exe dist/
mv dist/ AidBand/
mv AidBand/aidband.exe AidBand/AidBand.exe
#tar -cvzf AidBand.tar.gz AidBand
#rm -Rf AidBand/
