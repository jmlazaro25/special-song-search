#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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
        page = musicbrainzngs.search_artists('', country=country_code, )
        page_artists = page['artist-list']
        artists += page_artists

    return pd.DataFrame(artists)        

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

def sql():
    pass

if __name__ == '__main__':
    main()

