#!/usr/bin/env python
# coding: utf-8


from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy import Float
from sqlalchemy.engine.row import RowMapping

from special_song_search.database import init_db
from special_song_search.models import (
    artist_recording_association,
    Artist, ArtistTag,
    Recording, RecordingTag
)


def recommend(
        session,
        artist_tags: dict[str, float] = dict(),
        recording_tags: dict[str, float] = dict(),
        recording_length: tuple[int] = tuple(),
        recording_dates: tuple[str] = tuple(),
        weights: dict[str, float] = dict(),
        randomness: float = 1.,
        random_normal: float = 2.**64,
        limit: int = 10
    ) -> list[dict]:

    artist_tags_score = 0.0
    for tag, tag_weight in artist_tags.items():
        artist_tags_score += (ArtistTag.tag == tag) * tag_weight

    recording_tags_score = 0.0
    for tag, tag_weight in recording_tags.items():
        recording_tags_score += (RecordingTag.tag == tag) * tag_weight

    recording_length_score = 0.0
    if len(recording_length) == 1:
        recording_tags_score += func.abs(Recording.length - recording_length[0])

    score  = (
        func.cast(0, Float) # sqlalchemy func needed for label
        + artist_tags_score * weights.get('artist_tags', 0.0)
        + recording_tags_score * weights.get('recording_tags', 0.0)
        + recording_length_score * weights.get('recording_length', 0.0)
        #+ recording_dates_score * weights.get('recording_dates', 0.0)
    ).label('score')

    filter_score = (
        score
        + func.cast(func.random()/random_normal * randomness, Float)
    ).label('filter_score')

    statement = select(Recording, score, filter_score)
    if 'artist_tags' in weights:
        statement = statement\
            .join(artist_recording_association,
                Recording.mbid == artist_recording_association.c.recording_mbid)\
            .join(Artist, artist_recording_association.c.artist_mbid == Artist.mbid)\
            .join(ArtistTag, Artist.mbid == ArtistTag.artist_mbid)
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

