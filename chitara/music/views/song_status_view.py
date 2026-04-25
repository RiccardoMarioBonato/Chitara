from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..models import Song


@require_GET
def get_song_status(request, song_id):
    try:
        song = Song.objects.get(pk=song_id, user=request.user)
    except Song.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse({
        "song_id": song.pk,
        "status": song.generation_status,
        "audio_url": song.audio_url,
        "image_url": getattr(song, "image_url", ""),
        "duration_seconds": song.duration,
    })
