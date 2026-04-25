import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import Count, QuerySet, Sum

from .models import GenerationStatus, Song
from .repositories import RepositoryError, SongRepository
from .suno_client import APIError, SunoAPIClient
from .strategies.factory import StrategyFactory
from .strategies.exceptions import (
    SunoOfflineError,
    SunoInsufficientCreditsError,
    SunoGenerationError as StrategyGenerationError,
)

logger = logging.getLogger(__name__)


class InvalidGenerationInput(Exception):
    pass


class SongGenerationError(Exception):
    pass


class SongGenerationService:

    def __init__(
        self,
        repository: Optional[SongRepository] = None,
        api_client: Optional[SunoAPIClient] = None,
    ) -> None:
        self.repository: SongRepository = repository or SongRepository()
        self.api_client: SunoAPIClient = api_client or SunoAPIClient()

    def generate_song(self, user: User, form_data: dict) -> Song:
        self._validate_request(form_data)

        song = Song(
            title=form_data['title'],
            user=user,
            singer_model=form_data['singer_model'],
            genre=form_data['genre'],
            mood=form_data['mood'],
            occasion=form_data['occasion'],
            review_notes=form_data.get('review_notes', ''),
            duration=form_data['duration'],
            generation_status=GenerationStatus.PENDING,
        )
        song = self.repository.save(song)

        if form_data.get('themes'):
            song.themes.set(form_data['themes'])

        logger.info('Generation started: song_id=%s user=%s title=%r', song.pk, user.pk, song.title)

        try:
            self.repository.update_generation_status(song, GenerationStatus.GENERATING)

            prompt = self._build_prompt(song)
            song_request = {
                'prompt': prompt,
                'title': song.title,
                'genre': str(song.genre),
                'mood': str(song.mood),
                'duration': song.duration,
            }

            strategy = StrategyFactory.get_strategy()
            logger.info('Dispatching to %s for song_id=%s', strategy, song.pk)

            if hasattr(strategy, '_poll_until_done'):
                result = strategy.generate(song_request, song_instance=song)
            else:
                result = strategy.generate(song_request)

            if result.get('task_id'):
                song.external_id = result['task_id']
                song.save(update_fields=['external_id'])

            if result.get('status') == 'SUCCESS' and result.get('audio_url'):
                self.repository.update_audio_url(song, result['audio_url'])
                self.repository.update_generation_status(song, GenerationStatus.COMPLETED)
                logger.info('Song %s completed immediately (mock/sync)', song.pk)
            elif result.get('status') == 'SUCCESS' and not result.get('audio_url'):
                # Strategy returned SUCCESS but no URL — save a fallback so the
                # song is always playable in mock mode.
                from django.conf import settings
                if getattr(settings, 'GENERATOR_STRATEGY', 'mock').lower() == 'mock':
                    from music.strategies.mock_strategy import MOCK_AUDIO_URL
                    self.repository.update_audio_url(song, MOCK_AUDIO_URL)
                    self.repository.update_generation_status(song, GenerationStatus.COMPLETED)
                    logger.warning('Song %s SUCCESS but no audio_url; saved mock fallback', song.pk)
            else:
                logger.info('Song %s queued for async generation', song.pk)

            return song

        except (SunoOfflineError, SunoInsufficientCreditsError, StrategyGenerationError) as exc:
            logger.exception('Strategy error for song_id=%s: %s', song.pk, exc)
            try:
                self.repository.update_generation_status(song, GenerationStatus.FAILED)
            except RepositoryError:
                pass
            raise SongGenerationError(f'Song generation failed: {exc}') from exc
        except Exception as exc:
            logger.exception('Generation failed for song_id=%s: %s', song.pk, exc)
            try:
                self.repository.update_generation_status(song, GenerationStatus.FAILED)
            except RepositoryError:
                pass
            raise SongGenerationError(f'Song generation failed: {exc}') from exc

    def get_user_songs(self, user: User) -> QuerySet:
        return self.repository.get_user_songs(user)

    def _validate_request(self, form_data: dict) -> None:
        title = form_data.get('title', '').strip()
        duration = form_data.get('duration')

        if not title or len(title) < 3:
            raise InvalidGenerationInput('Title must be at least 3 characters.')
        if len(title) > 255:
            raise InvalidGenerationInput('Title cannot exceed 255 characters.')
        if duration is None:
            raise InvalidGenerationInput('Duration is required.')
        try:
            duration_int = int(duration)
        except (ValueError, TypeError):
            raise InvalidGenerationInput('Duration must be a number.')
        if not (10 <= duration_int <= 300):
            raise InvalidGenerationInput(
                f'Duration must be between 10 and 300 seconds (got {duration_int}s).'
            )

        for field in ('singer_model', 'genre', 'mood', 'occasion'):
            if not form_data.get(field):
                raise InvalidGenerationInput(f'"{field.replace("_", " ").title()}" is required.')

    def _build_prompt(self, song: Song) -> str:
        theme_names = ', '.join(t.name for t in song.themes.all()) or 'no specific theme'
        prompt = (
            f'{song.title} | '
            f'Genre: {song.genre} | '
            f'Mood: {song.mood} | '
            f'Occasion: {song.occasion} | '
            f'Themes: {theme_names} | '
            f'Voice: {song.singer_model} | '
            f'Duration: {song.duration}s'
        )
        if song.review_notes:
            prompt += f' | Notes: {song.review_notes}'
        return prompt


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


def generate_song(song_request, force_mock=False, song_instance=None):
    strategy = StrategyFactory.get_strategy(force_mock=force_mock)
    if hasattr(strategy, '_poll_until_done') and song_instance is not None:
        return strategy.generate(song_request, song_instance=song_instance)
    return strategy.generate(song_request)
