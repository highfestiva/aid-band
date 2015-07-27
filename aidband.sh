#!/bin/bash

cd ${0%/*}

while true; do
	killall Consoleify 2> /dev/null > /dev/null
	cp --update -R /tmp/aidband_install/* ./
	rm -Rf /tmp/aidband_install/*
	./aidband.py
done
