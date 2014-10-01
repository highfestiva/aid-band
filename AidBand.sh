#!/bin/bash

while true; do
	cp --update -R ../AidBandInstall/* ./
	rm -Rf ../AidBandInstall/*
	./AidBand.exe
done
