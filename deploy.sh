#!/bin/bash
#Example script that deploys to \\Bocken\RnD\AidBand. A first manual instance
#would have to be copied manully to that location and started.

./build.sh
sed -i.bak 's/\r//g' dist/*
rm dist/*.bak
scp -P 2202 dist/* password sp_credentials dev@ikaruso:/tmp/aidband_install/
rm -Rf dist/
./remote_aidband.py -t ikaruso -p -c '<quit>'
sleep 6
./remote_aidband.py -t ikaruso -p -c '<F4>'
