#!/bin/bash

./build.sh
mv dist/*.sh dist/*.exe dist/*.zip //bocken/RnD/AidBandInstall/
rm -Rf dist/
./remote_aidband.py bocken '+-*/~\r' '<quit>'
sleep 2
./remote_aidband.py bocken '+-*/~\r' '<F4>'
