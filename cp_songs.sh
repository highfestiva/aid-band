#!/bin/bash

cd cache
rsync -e 'ssh -p 2202' -trv . panthera:/home/jonte/dev/aidband/cache
