import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import Count, QuerySet, Sum

from ..models import GenerationStatus, Song
from ..repositories import SongRepository

logger = logging.getLogger(__name__)


class SongLibraryService:

    def __init__(self, repository: Optional[SongRepository] = None) -> None:
        self.repository: SongRepository = repository or SongRepository()

    def get_library(self, user: User) -> QuerySet:
        return self.repository.get_user_songs(user)

    def search_songs(self, user: User, query: str) -> QuerySet:
        qs = self.repository.get_user_songs(user)
        if query:
            qs = qs.filter(title__icontains=query.strip())
        return qs

    def get_statistics(self, user: User) -> dict:
        qs = self.repository.get_user_songs(user)
        status_counts = {
            row['generation_status']: row['count']
            for row in qs.values('generation_status').annotate(count=Count('id'))
        }
        total_duration = qs.aggregate(total=Sum('duration'))['total'] or 0
        genre_row = (
            qs.values('genre__name')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        return {
            'total_songs': qs.count(),
            'completed': status_counts.get(GenerationStatus.COMPLETED, 0),
            'generating': status_counts.get(GenerationStatus.GENERATING, 0),
            'failed': status_counts.get(GenerationStatus.FAILED, 0),
            'pending': status_counts.get(GenerationStatus.PENDING, 0),
            'total_duration': total_duration,
            'favorite_genre': genre_row['genre__name'] if genre_row else None,
        }

    def delete_song(self, song_id: int, user: User) -> None:
        song = self.repository.get_song(song_id, user)
        logger.info('User %s deleting song id=%s', user.pk, song_id)
        self.repository.delete(song)

    def share_song(self, song_id: int, user: User) -> Song:
        song = self.repository.get_song(song_id, user)
        if not song.is_shared:
            song.is_shared = True
            self.repository.save(song)
            logger.info('Song %s shared by user %s', song_id, user.pk)
        return song

    def unshare_song(self, song_id: int, user: User) -> Song:
        song = self.repository.get_song(song_id, user)
        if song.is_shared:
            song.is_shared = False
            self.repository.save(song)
            logger.info('Song %s unshared by user %s', song_id, user.pk)
        return song
