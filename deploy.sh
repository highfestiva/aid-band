#!/bin/bash
# Example script that deploys to dev@ikaruso. A first instance
# would have to be copied manully to that location and started.

scp -P 2202 -r password sp_credentials run.sh *.py dev@ikaruso:/tmp/
./remote_aidband.py -t ikaruso -p -c '<quit>'
sleep 6
./remote_aidband.py -t ikaruso -p -c '<F4>'
