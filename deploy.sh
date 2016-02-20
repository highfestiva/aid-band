#!/bin/bash
#Example script that deploys to \\Bocken\RnD\AidBand. A first manual instance
#would have to be copied manully to that location and started.

./build.sh
sed -i.bak 's/\r//g' aidband_install/*
rm aidband_install/*.bak
cp password sp_credentials aidband_install/
scp -P 2202 -r aidband_install dev@ikaruso:/tmp/
rm -Rf aidband_install/
./remote_aidband.py -t ikaruso -p -c '<quit>'
sleep 6
./remote_aidband.py -t ikaruso -p -c '<F4>'
