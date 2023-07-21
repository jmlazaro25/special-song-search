#!/usr/bin/env python
# coding: utf-8

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy import Float
from sqlalchemy.engine.row import RowMapping

from special_song_search.database import init_db
from special_song_search.models import (
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
    ) -> list[RowMapping]:

    artist_tags_score = 0.0
    for tag, tag_weight in artist_tags.items()
        artist_tags_score += (ArtistTag.tag == tag) * tag_weight

    score  = (
        func.cast(func.random()/random_normal * randomness, Float)
        + artist_tags_score * weights.get('artist_tags', 0.0)
        + recording_tags_score * weights.get('recording_tags', 0.0)
        + recording_length_score * weights.get('recording_length', 0.0)
        + recording_dates_score * weights.get('recording_dates', 0.0)
    ).label('score')

    statement = select(Recording, score)
    if 'artist_tags' in weights:
        statement = statement.join(Artist).join(ArtistTag)
    if (('recording_tags' in weights)
            or ('recording_length' in weights)
            or ('recording_dates' in weights)):
        statement = statement.join(RecordingTag)

    limit = limit if limit < 100 else 100
    statement.order_by(score.desc()).limit(limit)

    results = session.execute(statement).fetchall()
    row_mappings = [row._mapping for row in results]

    return row_mappings
