import os
import time
from urllib.request import urlretrieve
from collections import defaultdict
from contextlib import contextmanager

import logging
import requests
import spotify.sync as spotify
from gmusicapi import Mobileclient as MobileClient
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_OAUTH2_TOKEN = os.environ.get('SPOTIFY_OAUTH2_TOKEN')

bad = False

if not SPOTIFY_CLIENT_ID:
    print('SPOTIFY_CLIENT_ID environment variable not set. Generate one at https://developer.spotify.com/dashboard/applications')
    bad = True

if not SPOTIFY_CLIENT_SECRET:
    print('SPOTIFY_CLIENT_SECRET environment variable not set. Generate one at https://developer.spotify.com/dashboard/applications')
    bad = True

if not SPOTIFY_OAUTH2_TOKEN:
    print('SPOTIFY_OAUTH2_TOKEN environment variable not set. Generate one at https://developer.spotify.com/console/put-following/ we require the scopes user-follow-modify and user-library-modify')
    bad = True

if bad:
    exit(1)

g_client = MobileClient()
while not g_client.oauth_login(MobileClient.FROM_MAC_ADDRESS):
    g_client.perform_oauth()

artists = defaultdict(set)
for song in g_client.get_all_songs():
    artist = song['artist'].strip()
    album = song['album'].strip()
    albumArtist = song['albumArtist'].strip()

    if albumArtist:
        artist = albumArtist
    artists[artist].add(album)

# because the spotify library doesn't have follow yet...
def follow(artist):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {SPOTIFY_OAUTH2_TOKEN}',
    }
    params = {
        'type': 'artist',
        'ids': artist.id,
    }
    res = requests.put(
        'https://api.spotify.com/v1/me/following',
        params=params,
        headers=headers,
    )

    if res.status_code != 204:
        log.fatal(res.json())

@contextmanager
def context():
    c = spotify.Client(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    u = spotify.User.from_token(c, SPOTIFY_OAUTH2_TOKEN)
    l = spotify.Library(c, u)
    yield c, u, l
    c.close()
    # there will still be errors about unclosed connections for some reason...

with context() as (s_client, s_user, s_library):
    for artist, albums in artists.items():
        s = s_client.search(artist, types=['artist'])['artists']

        for s_artist in s:
            if s_artist.name.strip() != artist:
                continue

            follow(s_artist)

            s_albums = {a.name: a for a in s_artist.get_all_albums()}
            same = albums & set(s_albums)
            if len(same) != len(albums):
                log.warning(f'Not all albums found {artist}: {albums - same}')

            if same:
                s_albums = [s_a for a, s_a in s_albums.items() if a in same]
                s_library.save_albums(*s_albums)
                log.debug(f'Followed {artist}')

            break
        else:
            log.error(f'Could not find {artist}')
