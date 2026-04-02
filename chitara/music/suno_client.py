"""
Suno AI API Client — suno_client.py
Handles all HTTP communication with the Suno API.
No Django models or ORM imports belong here.
"""

import logging
import time
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (overridable via Django settings)
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = 'https://api.sunoapi.org/api/v1'
DEFAULT_TIMEOUT  = 30
MAX_RETRIES      = 3
PROMPT_MAX_CHARS = 1000


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class APIError(Exception):
    """Raised when the Suno API returns an error or is unreachable."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# SunoAPIClient
# ---------------------------------------------------------------------------

class SunoAPIClient:
    """
    Thin HTTP wrapper around the Suno AI music-generation API.

    Configuration (required in settings.py / .env):
        SUNO_API_KEY      — API authentication key
        SUNO_API_BASE_URL — Base URL (default: https://api.sunoapi.org/api/v1)
        SUNO_API_TIMEOUT  — Request timeout in seconds (default: 30)

    Usage:
        client = SunoAPIClient()
        result = client.generate_song(prompt="...", duration=60)
        # result → {'id': ..., 'audio_url': ..., 'title': ..., 'duration': ...}
    """

    def __init__(self):
        """Initialize SUNO API client with credentials from Django settings"""
        self.api_key = settings.SUNO_API_KEY
        self.base_url = settings.SUNO_API_BASE_URL
        self.timeout = getattr(settings, 'SUNO_API_TIMEOUT', 30)
        self.max_retries = 3
        self.retry_delay = 1
        
        # Setup headers with authorization
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',   # ← ADD self. HERE!
            'Content-Type': 'application/json',
        }
        
        logger.info(f"SunoAPIClient initialized with base_url: {self.base_url}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_song(
        self,
        prompt: str,
        duration: int,
        model: str = 'default',
    ) -> dict:
        """
        Submit a new song-generation request to the Suno API.

        Args:
            prompt:   Descriptive text prompt for the AI.
            duration: Desired length in seconds (10–300).
            model:    Suno model name (default: 'default').

        Returns:
            dict — {id, audio_url, title, duration}

        Raises:
            ValueError: If the prompt fails validation.
            APIError:   On network or API-level failure after MAX_RETRIES.
        """
        self._validate_prompt(prompt)

        payload = {
            'prompt':   prompt,
            'duration': duration,
            'model':    model,
            'customMode': True,
        }

        # Attach the webhook URL only when one is configured (requires ngrok or
        # a real public URL — localhost is not reachable by Suno's servers).
        callback_url = getattr(settings, 'SUNO_CALLBACK_URL', '')
        if callback_url:
            payload['callBackUrl'] = callback_url
            logger.debug('Using callBackUrl: %s', callback_url)

        logger.info(
            'Suno generate_song: duration=%ss model=%s prompt_len=%s',
            duration, model, len(prompt),
        )

        response = self._make_request('POST', '/generate', json=payload)

        return {
            'id':        response.get('id'),
            'audio_url': response.get('audio_url', ''),
            'title':     response.get('title', ''),
            'duration':  response.get('duration', duration),
        }

    def get_song_status(self, task_id: str) -> dict:
        """
        Poll the generation status of a previously submitted request.

        Args:
            task_id: The generation ID returned by generate_song().

        Returns:
            dict — {status, audio_url}

        Raises:
            APIError: On network or API-level failure.
        """
        logger.debug('Polling Suno status for task_id=%s', task_id)
        response = self._make_request('GET', f'/generate/{task_id}')
        return {
            'status':    response.get('status'),
            'audio_url': response.get('audio_url', ''),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_prompt(self, prompt: str) -> None:
        """
        Verify the prompt is non-empty and within the API character limit.

        Raises:
            ValueError: If validation fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError('Suno prompt must not be empty.')
        if len(prompt) > PROMPT_MAX_CHARS:
            raise ValueError(
                f'Suno prompt is too long ({len(prompt)} chars); '
                f'maximum is {PROMPT_MAX_CHARS}.'
            )

    def _retry_request(
        self,
        method: str,
        url: str,
        json: Optional[dict],
        attempt: int,
    ) -> requests.Response:
        """
        Single HTTP attempt. Callers loop over _make_request.
        Separated for easier unit testing.
        """
        return requests.request(
            method,
            url,
            headers=self.headers,
            json=json,
            timeout=self.timeout,
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict] = None,
    ) -> dict:
        """
        Execute an HTTP request with exponential back-off retry logic.

        Retry schedule:
            Attempt 1 — immediate
            Attempt 2 — wait 2 s
            Attempt 3 — wait 4 s

        HTTP errors handled:
            401 — authentication failure (not retried)
            429 — rate limit (retried with back-off)
            5xx — server error (retried with back-off)

        Raises:
            APIError: After MAX_RETRIES exhausted or on non-retriable errors.
        """
        url = f'{self.base_url}{endpoint}'
        last_exc: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._retry_request(method, url, json, attempt)

                # -- Non-retriable: bad API key --
                if response.status_code == 401:
                    raise APIError(
                        'Suno API authentication failed — verify SUNO_API_KEY.',
                        status_code=401,
                    )

                # -- Rate-limited: back off and retry --
                if response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(
                        'Suno rate limit (attempt %s/%s). Retrying in %ss.',
                        attempt, MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue

                # -- Server error: retry --
                if response.status_code >= 500:
                    last_exc = APIError(
                        f'Suno server error {response.status_code}.',
                        status_code=response.status_code,
                    )
                    logger.warning(
                        'Suno %s error (attempt %s/%s).',
                        response.status_code, attempt, MAX_RETRIES,
                    )
                else:
                    # 2xx / 3xx / 4xx (other than 401/429)
                    response.raise_for_status()
                    logger.debug(
                        'Suno %s %s → %s', method, endpoint, response.status_code
                    )
                    return response.json()

            except APIError:
                raise  # 401 — bubble up immediately, no retry.
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                logger.warning(
                    'Suno timeout (attempt %s/%s): %s', attempt, MAX_RETRIES, exc
                )
            except requests.exceptions.ConnectionError as exc:
                last_exc = exc
                logger.warning(
                    'Suno connection error (attempt %s/%s): %s',
                    attempt, MAX_RETRIES, exc,
                )
            except Exception as exc:  # pragma: no cover
                last_exc = exc
                logger.exception('Unexpected Suno API error: %s', exc)

            # Back-off before next attempt (skip after final attempt)
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)

        raise APIError(
            f'Suno API failed after {MAX_RETRIES} attempts: {last_exc}'
        ) from last_exc
