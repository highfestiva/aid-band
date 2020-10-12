#!/usr/bin/env python3


from absong import ABSong
from glob import glob
from http.server import HTTPServer, BaseHTTPRequestHandler
import os.path
import random
import urllib.parse
import util


mimetypes = dict(webm='audio/webm', mp3='audio/mpeg', ogg='audio/ogg', m4a='audio/mp4')


class AidbandServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(open('player.html','rb').read())
            return
        elif self.path == '/random' or self.path.startswith('/song/'):
            lines = list(open('favorites.txt', 'r', encoding='utf-8'))[1:]
            if '/song/' in self.path:
                title = urllib.parse.unquote(self.path.replace('/song/','')).lower()
                lines = [l for l in lines if title in l.lower()]
            for _ in range(20):
                line = random.choice(lines)
                song = ABSong(line)
                wc = util._cachewildcard(song)
                for fn in glob(wc):
                    print('Web server returning "%s"' % song)
                    self.send_response(200)
                    mime = mimetypes[os.path.splitext(fn)[1][1:].lower()]
                    data = open(fn, 'rb').read()
                    self.send_header('Content-Type', mime)
                    self.send_header('Content-Length', len(data))
                    self.end_headers()
                    self.wfile.write(data)
                    return
        self.send_response(404)
        self.end_headers()


def run():
	httpd = HTTPServer(('0.0.0.0', 8800), AidbandServer)
	httpd.serve_forever()


def run_threaded():
    from killable import KillableThread
    KillableThread(target=run).start()


if __name__ == '__main__':
    run()
