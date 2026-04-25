import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitara.settings')
django.setup()

from music.models import SingerModel

# SUNO Voice Models (from SUNO API documentation)
SUNO_MODELS = [
    {
        'name': 'Soprano',
        'description': 'High-pitched female vocal - bright and clear'
    },
    {
        'name': 'Alto',
        'description': 'Mid-range female vocal - warm and rich'
    },
    {
        'name': 'Tenor',
        'description': 'High-pitched male vocal - strong and powerful'
    },
    {
        'name': 'Baritone',
        'description': 'Mid-range male vocal - deep and resonant'
    },
    {
        'name': 'Bass',
        'description': 'Low-pitched male vocal - deep and grounding'
    },
    {
        'name': 'Instrumental',
        'description': 'No vocals - instrumental only'
    },
    {
        'name': 'Electronic',
        'description': 'Electronic/synth voice'
    },
    {
        'name': 'Ambient',
        'description': 'Atmospheric background vocals'
    },
]

# Create models
for model_data in SUNO_MODELS:
    singer_model, created = SingerModel.objects.get_or_create(
        name=model_data['name'],
        defaults={'description': model_data['description']}
    )
    
    if created:
        print(f"Created: {model_data['name']}")
    else:
        print(f"Already exists: {model_data['name']}")

print(f"\nTotal SingerModels: {SingerModel.objects.count()}")