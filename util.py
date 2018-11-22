import string
import sys

alnum_letters = string.ascii_letters + string.digits + ' '
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
