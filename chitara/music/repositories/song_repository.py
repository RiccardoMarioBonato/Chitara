import logging

from django.contrib.auth.models import User
from django.db.models import QuerySet

from ..models import Song
from .exceptions import RepositoryError

logger = logging.getLogger(__name__)


class SongRepository:
    """Abstracts all Song-related database operations."""

    def save(self, song: Song) -> Song:
        try:
            song.save()
            logger.debug('Song saved: id=%s title=%r', song.pk, song.title)
            return song
        except Exception as exc:
            logger.exception('Failed to save song: %s', exc)
            raise RepositoryError(f'Could not save song: {exc}') from exc

    def get_song(self, song_id: int, user: User) -> Song:
        try:
            return Song.objects.get(pk=song_id, user=user)
        except Song.DoesNotExist:
            logger.warning('Song not found: id=%s user=%s', song_id, user.pk)
            raise

    def get_user_songs(self, user: User) -> QuerySet:
        return Song.objects.filter(user=user).order_by('-created_at')

    def get_songs_by_status(self, user: User, status: str) -> QuerySet:
        return Song.objects.filter(user=user, generation_status=status)

    def get_songs_by_genre(self, user: User, genre) -> QuerySet:
        return Song.objects.filter(user=user, genre=genre)

    def delete(self, song: Song) -> None:
        try:
            logger.info('Deleting song: id=%s title=%r', song.pk, song.title)
            song.delete()
        except Exception as exc:
            logger.exception('Failed to delete song id=%s: %s', song.pk, exc)
            raise RepositoryError(f'Could not delete song: {exc}') from exc

    def get_shared_songs(self) -> QuerySet:
        return Song.objects.filter(is_shared=True).order_by('-created_at')

    def update_generation_status(self, song: Song, status: str) -> Song:
        try:
            song.generation_status = status
            song.save(update_fields=['generation_status'])
            logger.debug('Song %s status → %s', song.pk, status)
            return song
        except Exception as exc:
            logger.exception('Failed to update status for song %s: %s', song.pk, exc)
            raise RepositoryError(f'Could not update generation status: {exc}') from exc

    def update_audio_url(self, song: Song, audio_url: str) -> Song:
        try:
            song.audio_url = audio_url
            song.save(update_fields=['audio_url'])
            logger.debug('Song %s audio_url saved', song.pk)
            return song
        except Exception as exc:
            logger.exception('Failed to update audio_url for song %s: %s', song.pk, exc)
            raise RepositoryError(f'Could not update audio URL: {exc}') from exc
