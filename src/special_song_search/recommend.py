#!/usr/bin/env python
# coding: utf-8


from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy import Float
from sqlalchemy import Date
from sqlalchemy.engine.row import RowMapping

from special_song_search.database import init_db
from special_song_search.models import (
    artist_recording_association,
    Artist, ArtistTag,
    Recording, RecordingTag
)


# Reused strings
RECORDING_LENGTH = 'recording_length'
RECORDING_DATE = 'recording_date'
CONDITION = 'condition'
RANGE = 'range'
CENTER = 'center'
POINTS_PER_SECOND = 'points_per_second'
POINTS_PER_YEAR = 'points_per_year'

def recommend(
        session,
        artist_tags: dict[str, float] = dict(),
        recording_tags: dict[str, float] = dict(),
        weights: dict[str, float] = dict(),
        recording_length: dict = dict(),
        recording_date: dict = dict(),
        recording_status: str = '',
        randomness: float = 1.,
        random_normal: float = 2.**64,
        limit: int = 100
    ) -> list[dict]:

    artist_tags_score = 0.0
    for tag, tag_weight in artist_tags.items():
        artist_tags_score += (ArtistTag.tag == tag) * tag_weight

    recording_tags_score = 0.0
    for tag, tag_weight in recording_tags.items():
        recording_tags_score += (RecordingTag.tag == tag) * tag_weight

    score  = (
        func.cast(0, Float) # sqlalchemy func needed for label
        + artist_tags_score * weights.get('artist_tags', 0.0)
        + recording_tags_score * weights.get('recording_tags', 0.0)
    )

    if recording_length[f'{RECORDING_LENGTH}_{CONDITION}'] == CENTER:
        score -= (
            func.abs(Recording.length / 1_000 - recording_length[CENTER])
            * recording_length[POINTS_PER_SECOND]
        )

    if recording_date[f'{RECORDING_DATE}_{CONDITION}'] == CENTER:
        score -= (
            func.abs(
                # Only year extract in cast because some rows only have years
                func.cast(Recording.date, Date) - recording_date[CENTER]
            )
            * recording_date[POINTS_PER_YEAR]
        )

    score = score.label('score')

    filter_score = (
        score
        + func.cast(func.random()/random_normal * randomness, Float)
    ).label('filter_score')

    statement = select(Recording, score, filter_score)

    if recording_length[f'{RECORDING_LENGTH}_{CONDITION}'] == RANGE:
        statement = statement.where(
            recording_length[RANGE][0] <= Recording.length / 1_000
        )
        if recording_length[RANGE][1] is not None:
            statement = statement.where(
                Recording.length / 1_000 <= recording_length[RANGE][1]
            )

    if recording_date[f'{RECORDING_DATE}_{CONDITION}'] == RANGE:
        statement = statement.where(
                # Only year extract in cast because some rows only have years
                recording_date[RANGE][0] <= func.cast(Recording.date, Date)
        )
        if recording_date[RANGE][1] is not None:
            statement = statement.where(
                 func.cast(Recording.date, Date) <= recording_date[RANGE][1]
            )

    if 'artist_tags' in weights:
        statement = (statement
            .join(artist_recording_association,
                Recording.mbid == artist_recording_association.c.recording_mbid
                )
            .join(Artist, artist_recording_association.c.artist_mbid == Artist.mbid)
            .join(ArtistTag, Artist.mbid == ArtistTag.artist_mbid)
        )
    if 'recording_tags' in weights:
        statement = statement.join(RecordingTag)

    limit = limit if limit < 100 else 100
    statement = statement.order_by(filter_score.desc()).limit(limit)

    results = session.execute(statement).fetchall()
    row_mappings = [row._mapping for row in results]
    recommendations = [
        {
            'filter_score': row_mapping['filter_score'],
            'score': row_mapping['score'],
            'recording': row_mapping['Recording'].__dict__,
            'artists': [artist.__dict__ for artist in row_mapping['Recording'].artists],
            'recording_tags': [tag.__dict__ for tag in row_mapping['Recording'].tags]
        }
        for row_mapping in row_mappings
    ]

    return recommendations

def get_tag_options(session, tag_type: str) -> list[str]:
    if tag_type == 'artist':
        table = ArtistTag
    elif tag_type == 'recording':
        table = RecordingTag
    results = session.execute(select(table.tag).distinct()).fetchall()
    return [result[0] for result in results]
