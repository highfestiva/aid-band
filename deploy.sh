#!/bin/bash
#Example script that deploys to \\Bocken\RnD\AidBand. A first manual instance
#would have to be copied manully to that location and started.

./build.sh
scp -p 2202 dist/* password sp_credentials jonte@ikaruso:~/dev/aidband/install/
rm -Rf dist/
./remote_aidband.py -t ikaruso -p -c '<quit>'
sleep 6
./remote_aidband.py -t ikaruso -p -c '<F4>'
