import os.path
import string
import sys

alnum_letters = string.ascii_letters + string.digits + ' '
datadir = '.'
phrase_letters = alnum_letters + ' '


def rawstr(s):
    return ''.join([ch for ch in s if ch in alnum_letters])


def rawphrase(s):
    s = ''.join([ch for ch in s if ch in phrase_letters])
    return ' '.join(s.split())


def str2prt(*args):
    s = ' '.join([str(a) for a in args])
    try:
        if 'linux' in sys.platform:
            return s
        else:
            return s.encode('cp850','ignore').decode('cp850')
    except UnicodeEncodeError:
        return s.encode('ascii','ignore').decode('ascii')


def _cachewildcard(song):
    s = str(song.artist) + '-' + song.name
    replacements = {'/':'_', '\\':'_', ':':'_', '?':'', '(':'', ')':'', '[':'', ']':'', '"':'', '*':'_', '\t':' ', '  ':' '}
    for a,b in replacements.items():
        s = s.replace(a,b)
    s = s.partition('...')[0].strip()
    s = os.path.join(datadir, 'cache/'+s+'.*')
    return s
