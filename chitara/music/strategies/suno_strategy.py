import logging
import threading
import time

import requests
from django.conf import settings

from .base import SongGeneratorStrategy
from .exceptions import (
    SunoGenerationError,
    SunoInsufficientCreditsError,
    SunoOfflineError,
)

logger = logging.getLogger(__name__)

SUNO_BASE_URL = "https://api.sunoapi.org/api/v1"
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 60

_PLACEHOLDER_URLS = {
    "",
    "https://your-ngrok-url.ngrok-free.app/generation/suno/callback/",
}


class SunoSongGeneratorStrategy(SongGeneratorStrategy):

    def __init__(self):
        self.api_key = getattr(settings, "SUNO_API_KEY", "")
        configured = getattr(settings, "SUNO_CALLBACK_URL", "")
        # Suno requires callBackUrl on every request; use a fallback when ngrok isn't running
        self.callback_url = configured if configured not in _PLACEHOLDER_URLS else "https://placeholder.chitara.app/callback/"

        if not self.api_key:
            logger.warning("SUNO_API_KEY is not set.")

    def generate(self, song_request, song_instance=None) -> dict:
        payload = self._build_payload(song_request)
        task_id = self._create_task(payload)
        logger.info("Suno task created: %s", task_id)

        if song_instance is not None:
            self._start_polling_thread(task_id, song_instance)

        return {
            "status": "PENDING",
            "audio_url": "",
            "image_url": "",
            "task_id": task_id,
            "duration_seconds": 0,
        }

    def _build_payload(self, song_request) -> dict:
        if isinstance(song_request, dict):
            prompt = song_request.get("prompt", "")
            title = song_request.get("title") or song_request.get("requested_title", "Untitled")
            genre = song_request.get("genre", "")
            mood = song_request.get("mood", "")
            duration = int(song_request.get("duration") or song_request.get("requested_duration_seconds", 30))
        else:
            prompt = getattr(song_request, "prompt", "")
            title = getattr(song_request, "title", "Untitled")
            genre = getattr(song_request, "genre", "")
            mood = getattr(song_request, "mood", "")
            duration = int(getattr(song_request, "duration", 30))

        return {
            "prompt": prompt,
            "style": f"{genre} {mood}".strip(),
            "title": title,
            "model": "V4_5ALL",
            "customMode": True,
            "instrumental": True,
            "duration": max(10, min(duration, 300)),
            "callBackUrl": self.callback_url,
        }

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _create_task(self, payload: dict) -> str:
        url = f"{SUNO_BASE_URL}/generate"
        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
        except requests.exceptions.ConnectionError as exc:
            raise SunoOfflineError(f"Cannot connect to Suno API: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise SunoOfflineError(f"Suno API timed out: {exc}") from exc

        try:
            body = response.json()
        except Exception:
            raise SunoGenerationError(f"Non-JSON response from Suno: {response.text[:200]}")

        code = body.get("code")
        msg = body.get("msg", "")

        if code == 402 or "credit" in msg.lower():
            raise SunoInsufficientCreditsError(f"Insufficient credits: {msg}")

        if code != 200:
            raise SunoGenerationError(f"Suno error {code}: {msg}")

        task_id = (body.get("data") or {}).get("taskId") or body.get("taskId")
        if not task_id:
            raise SunoGenerationError(f"No taskId in response: {body}")

        return str(task_id)

    def _poll_status(self, task_id: str) -> dict:
        url = f"{SUNO_BASE_URL}/generate/record-info"
        try:
            response = requests.get(url, params={"taskId": task_id}, headers=self._get_headers(), timeout=15)
        except requests.exceptions.RequestException as exc:
            raise SunoOfflineError(f"Poll failed for {task_id}: {exc}") from exc

        try:
            return response.json()
        except Exception:
            return {}

    def _extract_clip(self, poll_data: dict) -> dict | None:
        data = poll_data.get("data") or {}
        task_status = data.get("status", "")
        suno_data_list = (data.get("response") or {}).get("sunoData") or []

        if not suno_data_list:
            return None

        clip = suno_data_list[0]
        audio_url = clip.get("audioUrl") or clip.get("streamAudioUrl") or ""
        image_url = clip.get("imageUrl") or clip.get("sourceImageUrl") or ""

        return {
            "status": task_status,
            "audio_url": audio_url,
            "image_url": image_url,
            "duration": clip.get("duration") or 0,
        }

    def _is_terminal_status(self, status: str, audio_url: str) -> tuple[bool, bool]:
        s = status.upper()
        if "FAIL" in s or "ERROR" in s:
            return True, False
        if audio_url or s in ("SUCCESS", "COMPLETE", "FIRST_SUCCESS", "MUSIC_SUCCESS"):
            return True, True
        return False, False

    def _update_song(self, song_instance, clip: dict, success: bool):
        try:
            song_instance.refresh_from_db()
            song_instance.generation_status = "COMPLETED" if success else "FAILED"
            if success and clip:
                song_instance.audio_url = clip.get("audio_url", "")
                if hasattr(song_instance, "image_url"):
                    song_instance.image_url = clip.get("image_url", "")
                if clip.get("duration"):
                    song_instance.duration = int(clip["duration"])
            song_instance.save()
            logger.info("Song %s updated to %s", song_instance.pk, song_instance.generation_status)
        except Exception as exc:
            logger.error("Failed to update song %s: %s", song_instance.pk, exc)

    def _poll_until_done(self, task_id: str, song_instance):
        logger.info("Polling started for task %s", task_id)
        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            time.sleep(POLL_INTERVAL_SECONDS)
            try:
                poll_data = self._poll_status(task_id)
            except SunoOfflineError as exc:
                logger.warning("Poll error (attempt %d): %s", attempt, exc)
                continue

            clip = self._extract_clip(poll_data)
            if clip is None:
                continue

            status = clip.get("status", "")
            audio_url = clip.get("audio_url", "")
            logger.debug("Task %s: status=%r audio_ready=%s", task_id, status, bool(audio_url))

            is_terminal, is_success = self._is_terminal_status(status, audio_url)
            if is_terminal:
                self._update_song(song_instance, clip, is_success)
                logger.info("Task %s done after %d polls, success=%s", task_id, attempt, is_success)
                return

        logger.error("Polling timed out for task %s", task_id)
        self._update_song(song_instance, {}, success=False)

    def _start_polling_thread(self, task_id: str, song_instance):
        thread = threading.Thread(
            target=self._poll_until_done,
            args=(task_id, song_instance),
            daemon=True,
        )
        thread.start()
