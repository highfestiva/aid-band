#!/usr/bin/env python3

from urllib.request import urlopen

def search(country='se', count=50):
	url = 'https://spotifycharts.com/api/?recurrence=weekly&date=latest&offset=0&limit=%i&type=regional&country=%s' % (count, country)
	json = urlopen(url).read().decode()
	py = json.replace('true','True').replace('false','False').replace('null','None')
	toplist_dict = eval(py)
	result = []
	return [entry['track'] for entry in toplist_dict['entries']['items']]

if __name__ == '__main__':
	for track in search():
		print(track['name'], 'by', track['artists'][0]['name'])
