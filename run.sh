#!/bin/bash

cd ${0%/*}

while true; do
	killall mplayer 2> /dev/null > /dev/null
	killall Consoleify 2> /dev/null > /dev/null
	cp --update -R /tmp/aidband_install/* ./
	rm -Rf /tmp/aidband_install/*
	python3 aidband.py
	while [ "`ss |grep 3303`" != "" ]; do sleep 1; echo 'w8ing for port to auto-close'; done
done