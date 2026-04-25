import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')
django.setup()

import requests
from django.conf import settings
import json

print("=" * 60)
print("RAW SUNO API REQUEST/RESPONSE")
print("=" * 60)

api_key = settings.SUNO_API_KEY
base_url = settings.SUNO_API_BASE_URL

print(f"\n1. API Key: {api_key[:20]}...")
print(f"2. Base URL: {base_url}")

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}

payload = {
    'prompt': 'Test song about happiness',
    'duration': 30,
    'make_instrumental': False,
}

print(f"\n3. Request Headers:")
print(f"   Authorization: Bearer {api_key[:20]}...")
print(f"   Content-Type: application/json")

print(f"\n4. Request Payload:")
print(json.dumps(payload, indent=2))

print(f"\n5. Making POST request to {base_url}/generate")

try:
    response = requests.post(
        f'{base_url}/generate',
        json=payload,
        headers=headers,
        timeout=10
    )
    
    print(f"\nResponse received.")
    print(f"\n6. HTTP Status Code: {response.status_code}")
    print(f"7. Response Headers:")
    for key, value in response.headers.items():
        print(f"   {key}: {value}")
    
    print(f"\n8. Response Body (raw):")
    print(response.text)
    
    print(f"\n9. Response JSON:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"\nRequest failed.")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)