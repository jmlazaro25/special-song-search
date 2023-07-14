#!/usr/bin/env python
# coding: utf-8

import musicbrainzngs
import pandas as pd
from dotenv import load_dotenv
from os import environ


# API LIMITS
RATE = 1.0
NEW_REQUESTS = 1
SEARCH_BROWSE_LIMIT = 100

# SELF LIMITS (used to not spend too much time on any one artist)
MAX_ARTIST_RECORDINGS = 5000

# Environment
load_dotenv()

def main() -> None:
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--get-artists', dest='get_artists', type=int, default=0)
    parser.add_argument('--get-recordings', dest='get_recordings', type=int, default=0)
    parser.add_argument('-v', dest='verbose', action='store_true', default=False)
    args = parser.parse_args()

    connect_to_musicbrainz(verbose=args.verbose)

    # Early testing
    if args.get_artists:
        artists_us = get_artists_from_country('US', offset=0, artists_limit=args.get_artists, verbose=args.verbose)

    if args.get_recordings:
        fr = get_artist_recordings(artist_mbid=artists_us.iloc[1]['id'], verbose=args.verbose)

    return

def connect_to_musicbrainz(verbose: bool = False) -> None:
    if verbose:
        print('setting user agent')

    musicbrainzngs.auth(environ.get('MBUA_USERNAME'), environ.get('MBUA_PASSWORD'))
    musicbrainzngs.set_useragent(environ.get('MBUA_APP'), environ.get('MBUA_VERSION'), environ.get('MBUA_CONTACT'))
    musicbrainzngs.set_rate_limit(limit_or_interval=RATE, new_requests=NEW_REQUESTS)

    if verbose:
        print('User agent set')

    return

def get_artists_from_country(country_code: str, offset: int, artists_limit: int, verbose: bool = False) -> pd.DataFrame:
    page_limit = artists_limit // SEARCH_BROWSE_LIMIT + min(artists_limit % SEARCH_BROWSE_LIMIT, 1)

    artists = []
    for page_n in range(page_limit):
        if verbose:
            print(f'Getting artists from {country_code}, page {page_n}')
        page = musicbrainzngs.search_artists(query='', country=country_code)
        page_artists = page['artist-list']
        artists += page_artists

    return pd.DataFrame([artist_flattened(artist) for artist in artists])

def get_artist_info(artist_mbid: str, verbose: bool = False) -> pd.DataFrame:
    includes = ['tags', 'ratings']
    artist = musicbrainzngs.get_artist_by_id(id=artist_mbid, includes=includes)
    artist = artist_flattened(artist)
    return pd.DataFrame([artist])

def artist_flattened(artist: dict[str, dict]) -> dict[str, str]:
    artist_flat = dict()
    artist_keys_to_keep = ('id', 'type', 'name', 'disambiguation', 'gender', 'country', 'life-span', 'tag-list', 'rating')

    artist_nest = artist['artist'] if 'artist' in artist else artist
    for key, value in  artist_nest.items():
        if key not in artist_keys_to_keep:
            continue

        if isinstance(value, str):
            artist_flat[key] = value

        elif isinstance(value, dict):
            if key == 'rating':
                artist_flat['rating_votes'] = int(value['votes-count'])
                artist_flat['rating'] = float(value['rating'])
            if key == 'life-span':
                for time in ('begin', 'end'):
                    if time in value:
                        artist_flat[f'life_span_{time}'] = value[time]

        elif isinstance(value, list):
            if key == 'tag-list':
                tags = sorted(value, key=lambda x: (-int(x['count']), x['name']))
                for n, tag in enumerate(tags):
                    artist_flat[f'tag_{n}'] = tag['name']
                    artist_flat[f'tag_{n}_count'] = tag['count']

    return artist_flat

def get_artist_recordings(artist_mbid: str, verbose: bool = False) -> pd.DataFrame:
    recordings = []
    for page_n in range(MAX_ARTIST_RECORDINGS//SEARCH_BROWSE_LIMIT):
        if verbose:
            print(f'Getting recordings from artist {artist_mbid}, page {page_n}')
        page = musicbrainzngs.browse_recordings(artist=artist_mbid, limit=SEARCH_BROWSE_LIMIT, offset=page_n * SEARCH_BROWSE_LIMIT)
        page_recordings = page['recording-list']
        recordings += page_recordings

        if len(page_recordings) < SEARCH_BROWSE_LIMIT:
            break

    return pd.DataFrame(recordings)

def get_recording_info(recording_mbid: str, verbose: bool = False) -> pd.DataFrame:
    includes = ['tags', 'ratings']
    recording = musicbrainzngs.get_artist_by_id(id=artist_mbid, includes=includes)
    recording = artist_flattened(recording)
    return pd.DataFrame([recording])

def recording_flattened(recording: dict[str, dict]) -> dict[str, str]:
    recording_flat = dict()
    recording_keys_to_keep = ('id', 'title', 'length', 'disambiguation', 'tag-list', 'rating')

    recording_nest = recording['recording'] if 'recording' in recording else recording
    for key, value in  recording_nest.items():
        if key not in keys_to_keep:
            continue

    return recording_flat


if __name__ == '__main__':
    main()

