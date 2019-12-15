#!/bin/bash
# Example script that deploys to dev@ikaruso. A first instance
# would have to be copied manully to that location and started.

scp -P 2202 -r password sp_credentials *.sh *.py ext/ dev@panthera:/tmp/aidband_install/
./remote_aidband.py -t panthera -p -c '<quit>'
sleep 15
./remote_aidband.py -t panthera -p -c '<F4>'
