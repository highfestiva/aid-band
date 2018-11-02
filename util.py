import string

alnum_letters = string.ascii_letters + string.digits + ' '
phrase_letters = alnum_letters + ' '


def rawstr(s):
    return ''.join([ch for ch in s if ch in alnum_letters])

def rawphrase(s):
    return ''.join([ch for ch in s if ch in phrase_letters])
