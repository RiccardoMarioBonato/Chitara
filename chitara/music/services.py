"""
Business Logic Layer — services.py
All workflow orchestration, validation, and domain rules live here.
Services call repositories and API clients; they never touch the ORM directly.
"""

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


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class InvalidGenerationInput(Exception):
    """Raised when form / service-level input validation fails."""


class SongGenerationError(Exception):
    """Raised when the Suno AI API call fails or returns bad data."""


# ---------------------------------------------------------------------------
# SongGenerationService
# ---------------------------------------------------------------------------

class SongGenerationService:
    """
    Orchestrates the full song-generation workflow:
        validate → create DB record → build prompt → call API → update record.

    Dependencies are injected so the class is easy to unit-test with mocks.
    """

    def __init__(
        self,
        repository: Optional[SongRepository] = None,
        api_client: Optional[SunoAPIClient] = None,
    ) -> None:
        self.repository: SongRepository = repository or SongRepository()
        self.api_client: SunoAPIClient  = api_client  or SunoAPIClient()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_song(self, user: User, form_data: dict) -> Song:
        """
        Full generation workflow (atomic from the caller's perspective).

        Steps:
            1. Validate input
            2. Create Song row with status=PENDING
            3. Build AI prompt
            4. Call Suno API
            5. Save audio_url and set status=COMPLETED
            6. On any failure, set status=FAILED and re-raise

        Args:
            user:      The authenticated Django User requesting the song.
            form_data: Cleaned data dict from SongGenerationForm.

        Returns:
            The saved Song instance.

        Raises:
            InvalidGenerationInput: when validation fails.
            SongGenerationError:    when the API call fails.
        """
        self._validate_request(form_data)

        # --- Step 1: Create a PENDING record first so we have a PK ---
        song = Song(
            title             = form_data['title'],
            user              = user,
            singer_model      = form_data['singer_model'],
            genre             = form_data['genre'],
            mood              = form_data['mood'],
            occasion          = form_data['occasion'],
            review_notes      = form_data.get('review_notes', ''),
            duration          = form_data['duration'],
            generation_status = GenerationStatus.PENDING,
        )
        song = self.repository.save(song)

        # M2M must be set after the instance has a PK.
        if form_data.get('themes'):
            song.themes.set(form_data['themes'])

        logger.info(
            'Generation started: song_id=%s user=%s title=%r',
            song.pk, user.pk, song.title,
        )

        try:
            # --- Step 2: Mark as generating ---
            self.repository.update_generation_status(song, GenerationStatus.GENERATING)

            # --- Step 3: Build prompt and dispatch to the active strategy ---
            prompt = self._build_prompt(song)
            song_request = {
                'prompt': prompt,
                'title': song.title,
                'genre': str(song.genre),
                'mood': str(song.mood),
                'duration': song.duration,
            }

            strategy = StrategyFactory.get_strategy()
            logger.info(
                'Generation dispatched: song_id=%s strategy=%s',
                song.pk, strategy,
            )

            # SunoStrategy needs the Song instance to update DB from its background thread
            if hasattr(strategy, '_poll_until_done'):
                result = strategy.generate(song_request, song_instance=song)
            else:
                result = strategy.generate(song_request)

            # --- Step 4: Persist result ---
            # Store the external task ID so polling/callback can locate this song
            if result.get('task_id'):
                song.external_id = result['task_id']
                song.save(update_fields=['external_id'])

            if result.get('status') == 'SUCCESS' and result.get('audio_url'):
                # Mock strategy — audio is ready immediately
                self.repository.update_audio_url(song, result['audio_url'])
                self.repository.update_generation_status(song, GenerationStatus.COMPLETED)
                logger.info(
                    'Generation completed immediately: song_id=%s strategy=%s',
                    song.pk, strategy,
                )
            else:
                # Suno strategy — background thread will update when ready
                logger.info(
                    'Song %s is generating async (external_id=%s strategy=%s)',
                    song.pk, result.get('task_id', ''), strategy,
                )

            return song

        except (SunoOfflineError, SunoInsufficientCreditsError, StrategyGenerationError) as exc:
            logger.exception('Strategy error for song_id=%s: %s', song.pk, exc)
            try:
                self.repository.update_generation_status(song, GenerationStatus.FAILED)
            except RepositoryError:
                logger.exception(
                    'Could not mark song %s as FAILED after strategy error.', song.pk
                )
            raise SongGenerationError(f'Song generation failed: {exc}') from exc
        except Exception as exc:
            logger.exception(
                'Generation failed for song_id=%s: %s', song.pk, exc
            )
            try:
                self.repository.update_generation_status(song, GenerationStatus.FAILED)
            except RepositoryError:
                logger.exception(
                    'Could not mark song %s as FAILED after generation error.', song.pk
                )
            raise SongGenerationError(
                f'Song generation failed: {exc}'
            ) from exc

    def get_user_songs(self, user: User) -> QuerySet:
        """Return all songs owned by *user* via the repository."""
        return self.repository.get_user_songs(user)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_request(self, form_data: dict) -> None:
        """
        Service-level validation (independent of form validation).

        Raises:
            InvalidGenerationInput: on any rule violation.
        """
        title    = form_data.get('title', '').strip()
        duration = form_data.get('duration')

        if not title or len(title) < 3:
            raise InvalidGenerationInput('Title must be at least 3 characters.')
        if len(title) > 255:
            raise InvalidGenerationInput('Title cannot exceed 255 characters.')

        if duration is None:
            raise InvalidGenerationInput('Duration is required.')
        if not (10 <= int(duration) <= 300):
            raise InvalidGenerationInput('Duration must be between 10 and 300 seconds.')

        for required_field in ('singer_model', 'genre', 'mood', 'occasion'):
            if not form_data.get(required_field):
                raise InvalidGenerationInput(
                    f'"{required_field.replace("_", " ").title()}" is required.'
                )

    def _build_prompt(self, song: Song) -> str:
        """
        Assemble a descriptive text prompt from the song's attributes.

        Format:
            <title> | <genre> | <mood> | <occasion> | <themes>
        """
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

        logger.debug('Built prompt (len=%s): %s', len(prompt), prompt[:120])
        return prompt


# ---------------------------------------------------------------------------
# SongLibraryService
# ---------------------------------------------------------------------------

class SongLibraryService:
    """
    Manages the user's song library: listing, searching, statistics,
    sharing, and deletion.
    """

    def __init__(self, repository: Optional[SongRepository] = None) -> None:
        self.repository: SongRepository = repository or SongRepository()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_library(self, user: User) -> QuerySet:
        """Return the user's songs ordered newest-first."""
        return self.repository.get_user_songs(user)

    def search_songs(self, user: User, query: str) -> QuerySet:
        """
        Case-insensitive title search within the user's library.

        Args:
            user:  Authenticated user.
            query: Search string (empty string returns all songs).
        """
        qs = self.repository.get_user_songs(user)
        if query:
            qs = qs.filter(title__icontains=query.strip())
        return qs

    def get_statistics(self, user: User) -> dict:
        """
        Aggregate statistics for the user's library.

        Returns:
            {
                'total_songs':      int,
                'completed':        int,
                'generating':       int,
                'failed':           int,
                'pending':          int,
                'total_duration':   int,   # seconds
                'favorite_genre':   str | None,
            }
        """
        qs = self.repository.get_user_songs(user)

        status_counts = {
            row['generation_status']: row['count']
            for row in qs.values('generation_status').annotate(count=Count('id'))
        }

        total_duration = qs.aggregate(total=Sum('duration'))['total'] or 0

        # Most common genre (by name) among this user's songs
        genre_row = (
            qs.values('genre__name')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        favorite_genre = genre_row['genre__name'] if genre_row else None

        return {
            'total_songs':    qs.count(),
            'completed':      status_counts.get(GenerationStatus.COMPLETED,  0),
            'generating':     status_counts.get(GenerationStatus.GENERATING, 0),
            'failed':         status_counts.get(GenerationStatus.FAILED,     0),
            'pending':        status_counts.get(GenerationStatus.PENDING,    0),
            'total_duration': total_duration,
            'favorite_genre': favorite_genre,
        }

    def delete_song(self, song_id: int, user: User) -> None:
        """
        Delete a song after verifying ownership.

        Raises:
            Song.DoesNotExist:  if the song is not found for this user.
            PermissionError:    (reserved for future use — ownership is
                                 already enforced by get_song).
        """
        song = self.repository.get_song(song_id, user)
        logger.info('User %s deleting song id=%s', user.pk, song_id)
        self.repository.delete(song)

    def share_song(self, song_id: int, user: User) -> Song:
        """
        Mark a song as publicly shared.

        Raises:
            Song.DoesNotExist: if the song is not found for this user.
        """
        song = self.repository.get_song(song_id, user)

        if not song.is_shared:
            song.is_shared = True
            self.repository.save(song)
            logger.info('Song %s shared by user %s', song_id, user.pk)

        return song

    def unshare_song(self, song_id: int, user: User) -> Song:
        """Revoke public sharing for a song."""
        song = self.repository.get_song(song_id, user)

        if song.is_shared:
            song.is_shared = False
            self.repository.save(song)
            logger.info('Song %s unshared by user %s', song_id, user.pk)

        return song


# ---------------------------------------------------------------------------
# Standalone strategy-based generation function (Exercise 4)
# ---------------------------------------------------------------------------

def generate_song(song_request, force_mock=False, song_instance=None):
    """
    Delegate song generation to the active strategy.

    Args:
        song_request: dict or model instance with generation parameters.
        force_mock:   If True, bypass settings and use Mock strategy.
        song_instance: Django Song model instance for the background thread
                       to update (required for Suno async polling).

    Returns:
        dict: { status, audio_url, image_url, task_id, duration_seconds }

    Raises:
        SunoOfflineError, SunoInsufficientCreditsError, StrategyGenerationError
    """
    strategy = StrategyFactory.get_strategy(force_mock=force_mock)
    logger.info("[GenerationService] Calling %s.generate()", strategy)

    # SunoStrategy needs the Song instance to update DB from background thread
    if hasattr(strategy, '_poll_until_done') and song_instance is not None:
        return strategy.generate(song_request, song_instance=song_instance)

    return strategy.generate(song_request)
