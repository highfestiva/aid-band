#!/bin/bash

rm -Rf dist/
python3 -OO setup_fill.py py2exe --bundle 1
