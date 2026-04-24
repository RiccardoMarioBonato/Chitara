"""
Demo script -- Exercise 4: Strategy Pattern

Demonstrates both Mock and Suno strategies without running the full
Django web server. Run from the project root (where manage.py lives):

    python demo_strategy.py

This serves as the "minimal demonstration" evidence required by the exercise.
"""

import os
import sys
import django

# Bootstrap Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chitara.settings")

django.setup()

from music.strategies.factory import StrategyFactory
from music.strategies.mock_strategy import MockSongGeneratorStrategy
from music.strategies.suno_strategy import SunoSongGeneratorStrategy
from music.strategies.base import SongGeneratorStrategy
from music.strategies.exceptions import SunoOfflineError, SunoInsufficientCreditsError

# ---------------------------------------------------------------------------
# Sample song request (matches what the form would submit)
# ---------------------------------------------------------------------------
SAMPLE_REQUEST = {
    "prompt": "A calm lo-fi instrumental with soft piano and rain sounds",
    "title": "Rainy Study Session",
    "genre": "Lo-fi",
    "mood": "Calm",
    "duration": 30,
    "is_public": True,
}

SEP = "-" * 60


def demo_mock():
    print(SEP)
    print("DEMO 1: Mock Strategy")
    print(SEP)

    strategy = MockSongGeneratorStrategy()

    # Verify it inherits from abstract base class
    assert isinstance(strategy, SongGeneratorStrategy), \
        "MockSongGeneratorStrategy must extend SongGeneratorStrategy"
    print(f"  Strategy class   : {strategy.__class__.__name__}")
    print(f"  Is ABC subclass  : {isinstance(strategy, SongGeneratorStrategy)}")

    result = strategy.generate(SAMPLE_REQUEST)
    print(f"  Result status    : {result['status']}")
    print(f"  Audio URL        : {result['audio_url']}")
    print(f"  Duration (secs)  : {result['duration_seconds']}")
    print(f"  Task ID          : {repr(result['task_id'])} (empty = expected for mock)")
    assert result["status"] == "SUCCESS", "Mock must return SUCCESS"
    assert result["audio_url"], "Mock must return a non-empty audio_url"
    print("  [OK] Mock strategy passed all assertions\n")


def demo_factory_mock():
    print(SEP)
    print("DEMO 2: StrategyFactory -> Mock (GENERATOR_STRATEGY=mock)")
    print(SEP)
    from django.conf import settings
    original = getattr(settings, "GENERATOR_STRATEGY", "mock")
    settings.GENERATOR_STRATEGY = "mock"

    strategy = StrategyFactory.get_strategy()
    print(f"  Factory returned : {strategy.__class__.__name__}")
    assert isinstance(strategy, MockSongGeneratorStrategy)
    result = strategy.generate(SAMPLE_REQUEST)
    print(f"  Status           : {result['status']}")
    assert result["status"] == "SUCCESS"
    print("  [OK] Factory correctly selected Mock strategy\n")

    settings.GENERATOR_STRATEGY = original


def demo_factory_suno():
    print(SEP)
    print("DEMO 3: StrategyFactory -> Suno (GENERATOR_STRATEGY=suno)")
    print(SEP)
    from django.conf import settings
    original = getattr(settings, "GENERATOR_STRATEGY", "mock")
    settings.GENERATOR_STRATEGY = "suno"

    strategy = StrategyFactory.get_strategy()
    print(f"  Factory returned : {strategy.__class__.__name__}")
    assert isinstance(strategy, SunoSongGeneratorStrategy)
    assert isinstance(strategy, SongGeneratorStrategy), \
        "SunoSongGeneratorStrategy must extend SongGeneratorStrategy"
    print(f"  Is ABC subclass  : {isinstance(strategy, SongGeneratorStrategy)}")
    print(f"  API key loaded   : {'YES (set)' if strategy.api_key else 'NO (empty -- set SUNO_API_KEY in .env)'}")
    print("  [OK] Factory correctly selected Suno strategy\n")

    settings.GENERATOR_STRATEGY = original


def demo_suno_live():
    print(SEP)
    print("DEMO 4: Suno Strategy -- Live API call (requires SUNO_API_KEY)")
    print(SEP)
    from django.conf import settings
    api_key = getattr(settings, "SUNO_API_KEY", "")

    if not api_key or api_key == "your_suno_api_key_here":
        print("  [WARN] SUNO_API_KEY not set -- skipping live API test.")
        print("     Set SUNO_API_KEY in your .env file and re-run to test.\n")
        return

    strategy = SunoSongGeneratorStrategy()
    print(f"  Strategy         : {strategy.__class__.__name__}")
    print(f"  Submitting to    : https://api.sunoapi.org/api/v1/generate")
    print(f"  Payload          : {SAMPLE_REQUEST}")

    try:
        result = strategy.generate(SAMPLE_REQUEST)  # No song_instance -> no DB update
        print(f"  Status           : {result['status']}")
        print(f"  Task ID          : {result['task_id']}")
        assert result["status"] == "PENDING", "Suno must return PENDING initially"
        assert result["task_id"], "Suno must return a non-empty task_id"
        print("  [OK] Suno strategy created task successfully\n")

        # Poll once to show status retrieval works
        print("  Polling status once (waiting 6 seconds)...")
        import time
        time.sleep(6)
        poll_data = strategy._poll_status(result["task_id"])
        clip = strategy._extract_clip(poll_data)
        if clip:
            print(f"  Poll result      : status={clip['status']}")
        else:
            print("  Poll result      : (no clip data yet -- still processing)")
        print("  [OK] Status polling endpoint working\n")

    except SunoOfflineError as exc:
        print(f"  [FAIL] Suno offline: {exc}\n")
    except SunoInsufficientCreditsError as exc:
        print(f"  [FAIL] Insufficient credits: {exc}\n")
    except Exception as exc:
        print(f"  [FAIL] Error: {exc}\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CHITARA -- Exercise 4: Strategy Pattern Demo")
    print("=" * 60 + "\n")

    demo_mock()
    demo_factory_mock()
    demo_factory_suno()
    demo_suno_live()

    print(SEP)
    print("Demo complete. Use the output above as grading evidence.")
    print(SEP + "\n")
