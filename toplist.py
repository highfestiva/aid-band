#!/usr/bin/env python3


from urllib.request import urlopen
import requests


def search(country='se', count=50):
    url = 'http://spotifycharts.com/api/?recurrence=weekly&date=latest&offset=0&limit=%i&type=regional&country=%s' % (count, country)
    json = urlopen(url).read().decode()
    py = json.replace('true','True').replace('false','False').replace('null','None')
    toplist_dict = eval(py)
    result = []
    for e in toplist_dict['entries']['items']:
        track = e['track']
        result += [{    'name':         track['name'],
                        'popularity':   e['plays'],
                        'artists':      track['artists'],
                        'uri':          'spotify:track:'+track['id'],   }]
    return result


def ilikeradio(client=11197927, channel=3):
    url = 'https://app.khz.se/api/v2/timeline?channel_id=%s&client_id=%s&limit=40' % (channel, client)
    result = []
    for s in requests.get(url).json():
        track = s['song']
        print(f"{track['artist_name']} - {track['title']}")
        result += [{    'name':         track['title'],
                        'artists':      [{'name':track['artist_name']}],
                        'uri':          None }]
    return result


if __name__ == '__main__':
    for track in ilikeradio():
        print(track['name'], 'by', track['artists'][0]['name'])
