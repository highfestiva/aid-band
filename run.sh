#!/bin/bash

cd ${0%/*}

while true; do
	killall mplayer 2> /dev/null > /dev/null
	killall Consoleify 2> /dev/null > /dev/null
	mkdir /tmp/aidband_install/ 2> /dev/null
	chmod 777 /tmp/aidband_install/
	cp --update -R /tmp/aidband_install/* ./
	rm -Rf /tmp/aidband_install/*
	dos2unix *.py *.sh
	python3 -u aidband.py 2>&1 > log.txt
	while [ "`ss |grep 3303`" != "" ]; do sleep 1; echo 'w8ing for port to auto-close'; done
	sleep 10
done
