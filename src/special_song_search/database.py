#!/usr/bin/env python
# coding: utf-8


# Standard
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
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

    engine, Session = init_db(args.database, verbose=args.verbose)
    musicb.connect_to_musicbrainz(verbose=args.verbose)

    with Session() as session:
        fill_artists_and_recordings(
            session=session,
            country_code=args.country_code,
            n_artists=args.n_artists,
            n_recordings=args.n_recordings,
            verbose=args.verbose
        )

    return


def init_db(database: str = '', verbose: bool = False) -> tuple[Engine, sessionmaker]:
    if database == '':
        database = "sqlite:///test.db"
    if database == 'main':
        database = environ.get('DATABASE_STR')

    if verbose:
        print(f'Connecting to {database}')

    engine = create_engine(database, future=True)
    Session = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(bind=engine)

    if verbose:
        print('Connected')

    return engine, Session


def fill_artists_and_recordings(
        session,
        country_code,
        n_artists,
        n_recordings,
        fill_recordings: bool = True,
        verbose: bool = False
    ) -> None:

    if verbose:
        print('Filling artists and recordings')

    artists = fill_artists(session, country_code, n_artists, verbose)

    if fill_recordings:
        for artist in artists:
            fill_artist_recordings(session, artist, n_recordings, verbose)

    return

def fill_artists(
        session,
        country_code,
        n_artists,
        verbose: bool = False
    ) -> list[Artist]:

    if verbose:
        print('Filling artists')

    offset = session.execute(
        select(func.count('*')).where(Artist.country == country_code)
    ).first()[0]

    artists, artist_tags = zip(
        *musicb.get_artists_from_country(
            country_code=country_code,
            offset=offset,
            n_artists=n_artists
        )
    )

    artist_rows = [
        Artist(
            mbid=artist['id'],
            name=artist.get('name', None),
            disambiguation=artist.get('disambiguation', None),
            type=artist.get('type', None),
            gender=artist.get('gender', None),
            country=artist.get('country', None),
            life_span_begin=artist.get('life_span_begin', None),
            life_span_end=artist.get('life_span_end', None),
            rating_votes=artist.get('rating_votes', None),
            rating=artist.get('rating', None)
        )
        for artist in artists
    ]

    artist_tag_rows = [
        [
            ArtistTag(
                artist_mbid=artist_row.mbid,
                artist=artist_row,
                tag=tag['name'],
                tag_votes=tag['count']
            )
            for tag in tags
        ]
        for artist_row, tags in zip(artist_rows, artist_tags)
    ]

    session.add_all(artist_rows)
    for tag_rows in artist_tag_rows:
        session.add_all(tag_rows)
    session.commit()

    return artist_rows

def fill_artist_recordings(
        session,
        artist: Artist,
        n_recordings: int,
        verbose: bool = False,
    ) -> None:

    if verbose:
        print('Filling recordings')

    recordings, recording_tags = zip(
        *musicb.get_artist_recordings(
            artist_mbid=artist.mbid,
            n_recordings=n_recordings,
            verbose=verbose
        )
    )

    recording_rows = [
        Recording(
            mbid=recording['id'],
            title=recording.get('title', None),
            disambiguation=recording.get('disambiguation', None),
            length=recording.get('length', None),
            date=recording.get('date', None),
            rating_votes=recording.get('rating_votes', None),
            rating=recording.get('rating', None),
            release_status=recording.get('release_status', None)
        )
        for recording in recordings
    ]

    recording_tag_rows = [
        [
            RecordingTag(
                recording_mbid=recording_row.mbid,
                recording=recording_row,
                tag=tag['name'],
                tag_votes=tag['count']
            )
            for tag in tags
        ]
        for recording_row, tags in zip(recording_rows, recording_tags)
    ]

    # Commits in loop slow, but limiting factor is API rate
    # Don't want to have to redo valid adds which requires recalling API
    for recording_row, tag_rows in zip(recording_rows, recording_tag_rows):
        try:
            artist.recordings.add(recording_row)
            session.add_all(tag_rows)
            session.commit()
        except IntegrityError:
            session.rollback()
            recording = session.execute(
                select(Recording).where(Recording.mbid == recording_row.mbid)
            ).scalar()
            artist.recordings.add(recording)
            session.commit()

    return


if __name__ == '__main__':
    main()

