#!/usr/bin/env python
# coding: utf-8


from __future__ import annotations

from sqlalchemy import String
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


artist_recording_association = Table(
    'artist_recording_association',
    Base.metadata,
    Column('artist_mbid', ForeignKey('artist.mbid'), primary_key=True),
    Column('recording_mbid', ForeignKey('recording.mbid'), primary_key=True)
)


class Artist(Base):
    __tablename__ = 'artist'

    mbid: Mapped[str] = mapped_column(String(40), primary_key=True)
    tags: Mapped[set[ArtistTag]] = relationship(back_populates='artist')
    recordings: Mapped[set[Recording]] = relationship(
        secondary=artist_recording_association, back_populates='artists'
    )


class Recording(Base):
    __tablename__ = 'recording'

    mbid: Mapped[str] = mapped_column(String(40), primary_key=True)
    tags: Mapped[set[RecordingTag]] = relationship(back_populates='recording')
    artists: Mapped[set[Artist]] = relationship(
        secondary=artist_recording_association, back_populates='recordings'
    )

class ArtistTag(Base):
    __tablename__ = 'artist_tag'

    artist_mbid: Mapped[str] = mapped_column(String(40), ForeignKey('artist.mbid'), primary_key=True)
    tag: Mapped[str] = mapped_column(String(40), primary_key=True)
    artist: Mapped[Artist] = relationship(back_populates='tags')

class RecordingTag(Base):
    __tablename__ = 'recording_tag'

    recording_mbid: Mapped[str] = mapped_column(String(40), ForeignKey('recording.mbid'), primary_key=True)
    tag: Mapped[str] = mapped_column(String(40), primary_key=True)
    recording: Mapped[Recording] = relationship(back_populates='tags')

