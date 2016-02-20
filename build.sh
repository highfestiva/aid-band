#!/bin/bash

rm -Rf aidband_install/
mkdir aidband_install
#python3 -OO setup.py py2exe
cp aidband.sh *.py aidband_install/
echo -n 'ABC' > aidband_install/password
echo -n 'spotify_username~~~spotify_password' > aidband_install/sp_credentials
