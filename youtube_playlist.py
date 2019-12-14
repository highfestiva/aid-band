#!/usr/bin/env python3

from html import unescape
from memoize import threaded_memoize
import requests


@threaded_memoize(timeout=5*60)
def playlist(lst):
    found = {}
    r = requests.get(lst)
    url = None
    take_next = False
    for line in r.text.splitlines():
        links = line.split('"/watch?')
        for t in links[1:]:
            t = t.split('"')[0]
            url = 'https://youtube.com/watch?'+t
            orig_url = url = unescape(url)
            if 'list=' not in url:
                continue
            url = url.partition('\\')[0]
            urlparts = url.split('&')
            urlparts = [u for u in urlparts if not any(u.startswith(strt) for strt in 'list= index= feature= \0026'.split())]
            url = '&'.join(urlparts)
            idx = orig_url.partition('index=')[2].partition('&')[0]
            idx = int(idx) if idx else 1
        if url:
            sline = line.strip()
            if sline.startswith('<h4 class="'):
                take_next = True
            elif take_next:
                sline = unescape(sline.split('(')[0])
                artist, _, song = [e.strip() for e in sline.partition(' - ')]
                found[idx] = (artist, song, url)
                url = None
                take_next = False
    return [found[k] for k in sorted(found)]


if __name__ == '__main__':
    l = playlist('https://www.youtube.com/watch?v=otCpCn0l4Wo&list=RDotCpCn0l4Wo')
    print(l)
