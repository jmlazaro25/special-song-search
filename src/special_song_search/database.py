#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Standard
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy import func
from dotenv import load_dotenv
from os import environ

# Typing
from sqlalchemy.engine.base import Engine

# Custom
from special_song_search import musicb
from special_song_search.models import (
    Base,
    Artist, ArtistTag,
    Recording, RecordingTag
)

def main() -> None:
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('n_artists', type=int,
                        help='Number of artists to add to database')
    parser.add_argument('n_recordings', type=int,
                        help=('Max recordings per artist\n'
                              +'-1 to use max given in music'
                              +'Ignored if greater than max given in musicb.py'
                             )
                       )
    parser.add_argument('--country', dest='country_code', type=str, default='US',
                        help='Country from which to get artists to database')
    parser.add_argument('--database', dest='database', type=str, default='',
                        help=('Database connection string\n'
                              +'Empty string creates/uses sqlite test.db\n'
                              +"'main' creates/uses $DATABASE_STR - USE WITH CAUTION"
                             )
                        )
    parser.add_argument('-v', dest='verbose', action='store_true', default=False)
    args = parser.parse_args()

    engine, Session = init_db(args.database)
    musicb.connect_to_musicbrainz(verbose=args.verbose)

    with Session as session():
        fill_artists_and_recordings(
            Session=session,
            country=args.country
            n_artists=args.n_artists,
            n_recordings=args.n_recordings,
        )

    return


def init_db(database: str = '') -> tuple[Engine, sessionmaker]:
    if database == '':
        database = "sqlite:///test.db"
    if database == 'main':
        database = environ.get('DATABASE_STR')

    engine = create_engine(database, future=True)
    Session = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(bind=engine)
    return engine, Session


def fill_artists_and_recordings(
    session,
    country,
    n_artists,
    n_recordings: int = -1,
    fill_recordings: bool = True
    ) -> None:

    offset = session.execute(
        select(func.count('*')).where(Artist.country == country)
    ).first()[0]
    artists = musicb.get_artists_from_country(country, offset=offset, artists_limit=n_artists)
    session.add_all([Artist(**artist) for artist in artists])
    session.commit()

    return

def fill

def fill_artist_recordings(
        session,
        artist_mbid: str,
        n_recordings: int = -1
    ) -> None:
    fr = musicb.get_artist_recordings(artist_mbid=artists_us.iloc[1]['id'], verbose=args.verbose)

if __name__ == '__name__':
    main()

