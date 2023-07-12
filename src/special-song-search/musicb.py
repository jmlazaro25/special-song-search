#!/usr/bin/env python
# coding: utf-8

import musicbrainzngs
import dotenv
import pandas as pd


# API LIMITS
RATE = 1.0
NEW_REQUESTS = 1
SEARCH_BROWSE_LIMIT = 100

# SELF LIMITS (used to not spend too much time on any one entity)
ARTIST_RECORDING_PAGES = 50

# Environment
ENV = dotenv.dotenv_values()

def main() -> None:
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--get-artists', dest='get_artists', action='store_true', default=False)
    parser.add_argument('--get-recordings', dest='get_recordings', action='store_true', default=False)
    parser.add_argument('-v', dest='verbose', action='store_true', default=False)
    args = parser.parse_args()

    connect_to_musicbrainz(verbose=args.verbose)

    if args.get_artists:
        artists_us = get_artists_from_country('US', offset=0, artists_limit=500, verbose=args.verbose)

    if args.get_recordings:
        fr = get_artist_recordings(artist_mbid=artists_us.iloc[1]['id'], verbose=args.verbose)

    return

def connect_to_musicbrainz(verbose: bool = False) -> None:
    if verbose:
        print('setting user agent')

    musicbrainzngs.auth(ENV['MBUA_USERNAME'], ENV['MBUA_PASSWORD'])
    musicbrainzngs.set_useragent(ENV['MBUA_APP'], ENV['MBUA_VERSION'], ENV['MBUA_CONTACT'])
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

    

    return pd.DataFrame(artists)

def get_artist_info(artist_mbid: str, verbose: bool = False) -> pd.DataFrame:
    includes = ['instrument-rels', 'tags', 'user-tags', 'ratings']
    artist = musicbrainzngs.get_artist_by_id(id=artist_mbid, includes=includes)
    artist = artist_flattened(artist)
    return pd.DataFrame([artist])

def artist_flattened(artist: dict[str, dict]) -> dict[str, str]:
    artist_flat = dict()
    artist_keys_to_keep = ('id', 'type', 'name', 'disambiguation', 'sort-name', 'gender', 'country', 'life-span', 'tag-list', 'rating')
    for key, value in  artist['artist'].items():
        if key in keys_to_keep:
            if isinstance(value, str):
                artist_flat[key] = value

            elif isinstance(value, dict):
                if key == 'rating':
                    artist_flat['rating-votes-count'] = value['votes-count']
                    artist_flat['rating'] = value['rating']
                if key == 'life-span':
                    for time in ('begin', 'end'):
                        if time in value:
                            artist_flat[f'life-span-{time}'] = value[time]

            elif isinstance(value, list):
                if key == 'tag-list':
                    # Only use top 10 tags
                    tags = sorted(value, key=lambda x: (-int(x['count']), x['name']))[:10]
                    for n, tag in enumerate(tags):
                        artist_flat[f'tag_{n}'] = tag['name']
                        artist_flat[f'tag_{n}_count'] = tag['count']

    return artist_flat

def get_artist_recordings(artist_mbid: str, verbose: bool = False) -> pd.DataFrame:
    recordings = []
    for page_n in range(ARTIST_RECORDING_PAGES):
        if verbose:
            print(f'Getting recordings from artist {artist_mbid}, page {page_n}')
        page = musicbrainzngs.browse_recordings(artist=artist_mbid, limit=SEARCH_BROWSE_LIMIT, offset=page_n * SEARCH_BROWSE_LIMIT)
        page_recordings = page['recording-list']
        recordings += page_recordings

        if len(page_recordings) < SEARCH_BROWSE_LIMIT:
            break

    return pd.DataFrame(recordings)

def get_recording_info(recording_mbid: str, verbose: bool = False) -> pd.DataFrame:
    includes = ['instrument-rels', 'tags', 'user-tags', 'ratings']
    recording = musicbrainzngs.get_artist_by_id(id=artist_mbid, includes=includes)
    recording = artist_flattened(recording)
    return pd.DataFrame([recording])

def recording_flattened(artist: dict[str, dict]) -> dict[str, str]:
    recording_flat = dict()
    return artist_flat

def sql():
    pass


if __name__ == '__main__':
    main()

