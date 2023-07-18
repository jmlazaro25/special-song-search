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
    parser.add_argument('n_artists', type=int)
    parser.add_argument('n_recordings', type=int)
    parser.add_argument('-v', dest='verbose', action='store_true', default=False)
    args = parser.parse_args()

    connect_to_musicbrainz(verbose=args.verbose)

    # Early testing
    artists = get_artists_from_country(
            'US', offset=1000, n_artists=args.n_artists, verbose=args.verbose)
    globals().update({'artists': artists})

    recs = get_artist_recordings(
            artist_mbid=artists[0][0]['id'], n_recordings=args.n_recordings, verbose=args.verbose)
    globals().update({'recs': recs})

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

def get_artists_from_country(
        country_code: str,
        n_artists: int,
        offset: int = 0,
        verbose: bool = False
    ) -> list[tuple]:
    n_pages = n_artists // SEARCH_BROWSE_LIMIT + min(n_artists % SEARCH_BROWSE_LIMIT, 1)

    artists = []
    for page_n in range(n_pages):
        if verbose:
            print(f'Getting artists from {country_code}, page {page_n}')
        page = musicbrainzngs.search_artists(
            query='',
            country=country_code,
            offset=offset + page_n * SEARCH_BROWSE_LIMIT,
            limit=SEARCH_BROWSE_LIMIT
        )
        page_artists = page['artist-list']
        artists += page_artists

    return [artist_flattened(artist) for artist in artists]

def get_artist_info(artist_mbid: str) -> dict:
    """ Get detailed artist information given mbid """
    includes = ['ratings']

    return musicbrainzngs.get_artist_by_id(id=artist_mbid, includes=includes)

def artist_flattened(artist: dict) -> tuple[dict, list]:
    artist_keys_to_keep = {'id', 'type', 'name', 'disambiguation', 'gender',
                           'country', 'life-span', 'tag-list', 'rating'}

    artist_flat = dict()
    artist_tags = []
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
            elif key == 'life-span':
                for time in ('begin', 'end'):
                    if time in value:
                        artist_flat[f'life_span_{time}'] = value[time]

        elif isinstance(value, list):
            if key == 'tag-list':
                artist_tags = value

    return artist_flat, artist_tags

def get_artist_recordings(
        artist_mbid: str,
        n_recordings: int = -1,
        detailed: bool = True,
        verbose: bool = False
    ) -> list[tuple]:
    includes = ['artist-credits', 'tags', 'ratings']

    if n_recordings != -1 and n_recordings < MAX_ARTIST_RECORDINGS:
        n_pages = n_recordings // SEARCH_BROWSE_LIMIT + min(n_recordings % SEARCH_BROWSE_LIMIT, 1)
    else:
        n_pages = MAX_ARTIST_RECORDINGS // SEARCH_BROWSE_LIMIT

    recordings = []
    for page_n in range(n_pages):
        if verbose:
            print(f'Getting recordings from artist {artist_mbid}, page {page_n}')
        page = musicbrainzngs.browse_recordings(
            artist=artist_mbid,
            includes=includes,
            offset=page_n * SEARCH_BROWSE_LIMIT,
            limit=SEARCH_BROWSE_LIMIT
        )
        page_recordings = page['recording-list']
        recordings += page_recordings

        if len(page_recordings) < SEARCH_BROWSE_LIMIT:
            break

    if detailed:
        if verbose:
            print('Getting recording(s) details')
        mbids = [recording['id'] for recording in recordings]
        return [recording_flattened(get_recording_info(mbid)) for mbid in mbids]

    return [recording_flattened(recording) for recording in recordings]

def get_recording_info(recording_mbid: str) -> dict:
    """ Get detailed recording information given mbid """
    includes = ['releases', 'artist-credits', 'tags', 'ratings']
    release_type = ['album', 'single', 'ep']
    release_status = ['official']

    return musicbrainzngs.get_recording_by_id(
        id=recording_mbid,
        includes=includes,
        release_type=release_type,
        release_status=release_status
    )

def recording_flattened(recording: dict) -> tuple[dict, list]:
    recording_keys_to_keep = {'id', 'title', 'length', 'disambiguation',
                              'release-list', 'tag-list', 'rating',
                              'artist-credit-phrase'}

    recording_flat = dict()
    recording_tags = []
    recording_nest = recording['recording'] if 'recording' in recording else recording

    for key, value in  recording_nest.items():
        if key not in recording_keys_to_keep:
            continue

        if isinstance(value, str):
            if key == 'length':
                recording_flat[key] = int(value)
            else:
                recording_flat[key] = value

        elif isinstance(value, dict):
            if key == 'rating':
                recording_flat['rating_votes'] = int(value['votes-count'])
                recording_flat['rating'] = float(value['rating'])

        elif isinstance(value, list):
            if (key == 'release-list') and value:
                first_release = min(
                    value,
                    key=lambda release: release.get('date', '99999')
                )
                recording_flat['date'] = first_release.get('date', None)
                recording_flat['release_status'] = 'official'
            elif key == 'tag-list':
                recording_tags = value

    return recording_flat, recording_tags


if __name__ == '__main__':
    main()

