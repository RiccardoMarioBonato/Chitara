import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet

from ..models import GenerationStatus, Song
from ..strategies.mock_strategy import MOCK_AUDIO_URL
from ..repositories import RepositoryError, SongRepository
from ..suno_client import APIError, SunoAPIClient
from ..strategies.exceptions import (
    SunoGenerationError as StrategyGenerationError,
    SunoInsufficientCreditsError,
    SunoOfflineError,
)
from ..strategies.factory import StrategyFactory
from .exceptions import InvalidGenerationInput, SongGenerationError

logger = logging.getLogger(__name__)


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

            if result.get('status') == 'SUCCESS':
                self.repository.update_audio_url(song, result.get('audio_url') or MOCK_AUDIO_URL)
                self.repository.update_generation_status(song, GenerationStatus.COMPLETED)
                logger.info('Song %s completed immediately (mock/sync)', song.pk)
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
        if duration is None or duration == '':
            raise InvalidGenerationInput('Duration is required.')
        try:
            duration_int = int(duration)
        except (ValueError, TypeError):
            raise InvalidGenerationInput('Duration must be a number.')
        if not (30 <= duration_int <= 300):
            raise InvalidGenerationInput(
                f'Duration must be between 30 and 300 seconds (got {duration_int}s).'
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
