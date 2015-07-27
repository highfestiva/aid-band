#!/bin/bash

rm -Rf dist/
mkdir dist
#python3 -OO setup.py py2exe
#cp /c/Program\ Files\ \(x86\)/mplayer/mplayer.exe dist/
cp *.py dist/
#mv dist/aidband.exe dist/AidBand.exe
#cp Consoleify.exe OpenAL.dll libspotify.dll dist/
echo -n 'ABC' > dist/password
echo -n 'spotify_username~~~spotify_password' > dist/sp_credentials
