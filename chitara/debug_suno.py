import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')
django.setup()

from music.suno_client import SunoAPIClient
from django.conf import settings
import json

print("=" * 60)
print("SUNO API DEBUG")
print("=" * 60)

print(f"\n1. API Key (first 20 chars): {settings.SUNO_API_KEY[:20]}...")
print(f"2. Base URL: {settings.SUNO_API_BASE_URL}")

print(f"\n3. Creating client...")
client = SunoAPIClient()
print(f"   ✅ Client created")

print(f"\n4. Calling SUNO API...")
try:
    result = client.generate_song(
        prompt="Test song about happiness and love",
        duration=30
    )
    
    print(f"\n✅ API RESPONSE:")
    print(json.dumps(result, indent=2))
    
    print(f"\n📊 Response fields:")
    for key, value in result.items():
        print(f"   - {key}: {value}")
    
    if result.get('audio_url'):
        print(f"\n✅ Audio URL found!")
    else:
        print(f"\n❌ NO AUDIO URL in response!")
        
except Exception as e:
    print(f"\n❌ ERROR:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)