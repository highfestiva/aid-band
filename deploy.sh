#!/bin/bash
#Example script that deploys to \\Bocken\RnD\AidBand. A first manual instance
#would have to be copied manully to that location and started.

./build.sh
cp dist/* password sp_credentials //bocken/RnD/AidBandInstall/
rm -Rf dist/
./remote_aidband.py -t bocken -p -c '<quit>'
sleep 6
./remote_aidband.py -t bocken -p -c '<F4>'
