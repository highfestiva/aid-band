#!/usr/bin/env python3
# -*- coding:utf-8 -*-

class ABSong:
	def __init__(self, _name,_artist,_uri):
		self.name = _name
		self.artist = str(_artist)
		self.uri = _uri
	def __eq__(self, other):
		return self.name == other.name and self.artist == str(other.artist)
