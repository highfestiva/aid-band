class ABSong:
	def __init__(self, _name,_artist,_url):
		self.name = _name
		self.artist = str(_artist)
		class ABStream:
			pass
		self.stream = ABStream()
		self.stream.url = _url
	def __eq__(self, other):
		return self.name == other.name and self.artist == str(other.artist)
