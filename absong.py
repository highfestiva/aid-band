#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from util import rawphrase


class ABSong:
    def __init__(self, _name,_artist,_uri):
        self.name = _name
        self.artist = str(_artist)
        self.searchname   = self.name.lower()
        if self.searchname[0] != '(':
            self.searchname = self.searchname.partition('(')[0]
        self.searchname   = rawphrase(self.searchname)
        self.searchartist = rawphrase(self.artist.lower().split('+')[0])
        self.uri = _uri
    def __eq__(self, other):
        return self.name == other.name and self.artist == str(other.artist)
    def __str__(self):
        return self.artist + ' ' + self.name
    def __repr__(self):
        return self.__str__()
