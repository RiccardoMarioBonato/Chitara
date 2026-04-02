import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')
django.setup()

from music.models import Song

songs = Song.objects.all().order_by('-created_at')

print("=" * 60)
print("LATEST SONGS")
print("=" * 60)

for song in songs[:5]:
    print(f"\nSong ID: {song.id}")
    print(f"  Title: {song.title}")
    print(f"  Status: {song.status}")
    print(f"  External ID: {song.external_id}")
    print(f"  Audio URL: {song.audio_url}")
    print(f"  Created: {song.created_at}")

print("\n" + "=" * 60)