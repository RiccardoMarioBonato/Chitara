import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..models import GenerationStatus, Song

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SunoCallbackView(View):

    def post(self, request):
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id') or data.get('id')
            audio_url = data.get('audio_url', '')

            if task_id:
                song = Song.objects.filter(external_id=task_id).first()
                if song:
                    song.audio_url = audio_url
                    song.generation_status = GenerationStatus.COMPLETED
                    song.save(update_fields=['audio_url', 'generation_status'])
                    logger.info('Song %s updated via callback (task_id=%s)', song.id, task_id)
                else:
                    logger.warning('No song found with external_id=%s', task_id)

            return JsonResponse({'status': 'received'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
