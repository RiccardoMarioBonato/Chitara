import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')
django.setup()

from music.suno_client import SunoAPIClient
from django.conf import settings

print("=" * 50)
print("SUNO API TEST")
print("=" * 50)

print(f"\n1. API Key loaded: {bool(settings.SUNO_API_KEY)}")
print(f"   Key (first 20 chars): {settings.SUNO_API_KEY[:20] if settings.SUNO_API_KEY else 'NONE'}...")

print(f"\n2. Base URL: {settings.SUNO_API_BASE_URL}")

print(f"\n3. Testing SunoAPIClient initialization...")
try:
    client = SunoAPIClient()
    print(f"   Client initialized.")
    print(f"   - API Key in client: {bool(client.api_key)}")
    print(f"   - Base URL: {client.base_url}")
except Exception as e:
    print(f"   Error: {e}")

print(f"\n4. Testing API call...")
try:
    client = SunoAPIClient()
    result = client.generate_song(
        prompt="Test song about happiness and love",
        duration=30
    )
    print(f"   API Call successful.")
    print(f"   Response: {result}")
except Exception as e:
    print(f"   API Call failed.")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")

print("\n" + "=" * 50)