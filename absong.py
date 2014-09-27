class ABSong:
	def __init__(self, _name,_artist,_url):
		self.name = _name
		self.artist = _artist
		class ABStream:
			pass
		self.stream = ABStream()
		self.stream.url = _url
