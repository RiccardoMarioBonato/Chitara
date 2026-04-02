"""
Persistence Layer — repositories.py
All direct database access is isolated here.
HTTP / API concerns live in suno_client.py instead.
"""

import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet

from .models import Song
from .suno_client import APIError  # re-exported so services only need one import  # noqa: F401

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class RepositoryError(Exception):
    """Raised when a database operation fails unexpectedly."""


# ---------------------------------------------------------------------------
# SongRepository
# ---------------------------------------------------------------------------

class SongRepository:
    """
    Abstracts all Song-related database operations.

    Views and services must NOT import Song.objects directly;
    they must go through this class so persistence logic stays in one place.
    """

    def save(self, song: Song) -> Song:
        """Persist a Song instance (insert or update)."""
        try:
            song.save()
            logger.debug('Song saved: id=%s title=%r', song.pk, song.title)
            return song
        except Exception as exc:
            logger.exception('Failed to save song: %s', exc)
            raise RepositoryError(f'Could not save song: {exc}') from exc

    def get_song(self, song_id: int, user: User) -> Song:
        """
        Return the Song with the given pk that belongs to *user*.

        Raises:
            Song.DoesNotExist: if no matching row is found.
        """
        try:
            return Song.objects.get(pk=song_id, user=user)
        except Song.DoesNotExist:
            logger.warning('Song not found: id=%s user=%s', song_id, user.pk)
            raise

    def get_user_songs(self, user: User) -> QuerySet:
        """Return all songs owned by *user*, newest first."""
        return Song.objects.filter(user=user).order_by('-created_at')

    def get_songs_by_status(self, user: User, status: str) -> QuerySet:
        """Return songs filtered by *status* for *user*."""
        return Song.objects.filter(user=user, generation_status=status)

    def get_songs_by_genre(self, user: User, genre) -> QuerySet:
        """Return songs filtered by *genre* for *user*."""
        return Song.objects.filter(user=user, genre=genre)

    def delete(self, song: Song) -> None:
        """Delete a Song instance from the database."""
        try:
            logger.info('Deleting song: id=%s title=%r', song.pk, song.title)
            song.delete()
        except Exception as exc:
            logger.exception('Failed to delete song id=%s: %s', song.pk, exc)
            raise RepositoryError(f'Could not delete song: {exc}') from exc

    def get_shared_songs(self) -> QuerySet:
        """Return all songs that have been shared publicly."""
        return Song.objects.filter(is_shared=True).order_by('-created_at')

    def update_generation_status(self, song: Song, status: str) -> Song:
        """Update only the generation_status field and save."""
        try:
            song.generation_status = status
            song.save(update_fields=['generation_status'])
            logger.debug('Song %s status → %s', song.pk, status)
            return song
        except Exception as exc:
            logger.exception(
                'Failed to update status for song %s: %s', song.pk, exc
            )
            raise RepositoryError(
                f'Could not update generation status: {exc}'
            ) from exc

    def update_audio_url(self, song: Song, audio_url: str) -> Song:
        """Store the audio URL returned by the Suno API."""
        try:
            song.audio_url = audio_url
            song.save(update_fields=['audio_url'])
            logger.debug('Song %s audio_url saved', song.pk)
            return song
        except Exception as exc:
            logger.exception(
                'Failed to update audio_url for song %s: %s', song.pk, exc
            )
            raise RepositoryError(
                f'Could not update audio URL: {exc}'
            ) from exc
