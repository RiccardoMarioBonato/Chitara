import logging
import time
from typing import Optional

import requests
from django.conf import settings

from .api_error import APIError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = 'https://api.sunoapi.org/api/v1'
DEFAULT_TIMEOUT  = 30
MAX_RETRIES      = 3
PROMPT_MAX_CHARS = 1000


class SunoAPIClient:
    """Thin HTTP wrapper around the Suno AI music-generation API."""

    def __init__(self):
        self.api_key  = settings.SUNO_API_KEY
        self.base_url = settings.SUNO_API_BASE_URL
        self.timeout  = getattr(settings, 'SUNO_API_TIMEOUT', 30)
        self.max_retries = 3
        self.retry_delay = 1

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        logger.info('SunoAPIClient initialized with base_url: %s', self.base_url)

    def generate_song(self, prompt: str, duration: int, model: str = 'default') -> dict:
        self._validate_prompt(prompt)

        payload = {
            'prompt':      prompt,
            'duration':    duration,
            'model':       model,
            'customMode':  True,
            'callBackUrl': settings.SUNO_CALLBACK_URL,
        }

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
        logger.debug('Polling Suno status for task_id=%s', task_id)
        response = self._make_request('GET', f'/generate/{task_id}')
        return {
            'status':    response.get('status'),
            'audio_url': response.get('audio_url', ''),
        }

    def _validate_prompt(self, prompt: str) -> None:
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
        return requests.request(
            method, url, headers=self.headers, json=json, timeout=self.timeout,
        )

    def _make_request(self, method: str, endpoint: str, json: Optional[dict] = None) -> dict:
        url = f'{self.base_url}{endpoint}'
        last_exc: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._retry_request(method, url, json, attempt)

                if response.status_code == 401:
                    raise APIError(
                        'Suno API authentication failed — verify SUNO_API_KEY.',
                        status_code=401,
                    )

                if response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning('Suno rate limit (attempt %s/%s). Retrying in %ss.', attempt, MAX_RETRIES, wait)
                    time.sleep(wait)
                    continue

                if response.status_code >= 500:
                    last_exc = APIError(f'Suno server error {response.status_code}.', status_code=response.status_code)
                    logger.warning('Suno %s error (attempt %s/%s).', response.status_code, attempt, MAX_RETRIES)
                else:
                    response.raise_for_status()
                    logger.debug('Suno %s %s → %s', method, endpoint, response.status_code)
                    return response.json()

            except APIError:
                raise
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                logger.warning('Suno timeout (attempt %s/%s): %s', attempt, MAX_RETRIES, exc)
            except requests.exceptions.ConnectionError as exc:
                last_exc = exc
                logger.warning('Suno connection error (attempt %s/%s): %s', attempt, MAX_RETRIES, exc)
            except Exception as exc:
                last_exc = exc
                logger.exception('Unexpected Suno API error: %s', exc)

            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)

        raise APIError(f'Suno API failed after {MAX_RETRIES} attempts: {last_exc}') from last_exc
