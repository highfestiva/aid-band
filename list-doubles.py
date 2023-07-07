#!/usr/bin/env python3

import argparse
import os


base2file = {}


def prt(s, options):
    if options.include:
        ok = False
        for i in options.include:
            ok |= i in s
        if not ok:
            return
    for e in options.exclude:
        if e in s:
            return
    try:
        print(s)
    except:
        print(str(s.encode())[2:-1])
    if options.remove:
        os.unlink(s)


for fn in os.listdir('cache'):
    fn = 'cache/' + fn
    base,ext = os.path.splitext(fn)
    if base not in base2file:
        base2file[base] = [fn]
    else:
        base2file[base].append(fn)


parser = argparse.ArgumentParser()
parser.add_argument('--singles-only', action='store_true', help='inverts the logic')
parser.add_argument('-i', '--include', nargs='*', default=[], help='filter to include, like .ogg')
parser.add_argument('-e', '--exclude', nargs='*', default=[], help='filter to exclude, like .webm')
parser.add_argument('--remove', action='store_true', help='remove files listed')
options = parser.parse_args()

for base,fns in sorted(base2file.items()):
    if options.singles_only:
        if len(fns) == 1:
            prt(fns[0], options)
    else:
        if len(fns) > 1:
            for fn in fns:
                prt(fn, options)
