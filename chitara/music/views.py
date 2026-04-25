import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .forms import SongGenerationForm
from .models import Feedback, GenerationStatus, Genre, Mood, Occasion, Song, Theme
from .services import (
    InvalidGenerationInput,
    SongGenerationError,
    SongGenerationService,
    SongLibraryService,
)

logger = logging.getLogger(__name__)


class SongGenerationView(LoginRequiredMixin, CreateView):
    model = Song
    form_class = SongGenerationForm
    template_name = 'music/song_form.html'

    def get_context_data(self, **kwargs) -> dict:
        from django.conf import settings as _s
        ctx = super().get_context_data(**kwargs)
        strategy = getattr(_s, 'GENERATOR_STRATEGY', 'mock').lower().strip()
        if not getattr(_s, 'SUNO_API_KEY', ''):
            strategy = 'mock'
        ctx.update({
            'genres': Genre.objects.all(),
            'moods': Mood.objects.all(),
            'occasions': Occasion.objects.all(),
            'themes': Theme.objects.all(),
            'generator_strategy': strategy,
        })
        return ctx

    def form_valid(self, form):
        post_data = {key: self.request.POST.getlist(key) for key in self.request.POST}
        self.request.session['song_preview_data'] = post_data
        return redirect(reverse_lazy('music:song-preview'))

    def form_invalid(self, form):
        if self._is_ajax():
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        return super().form_invalid(form)

    def get_success_url(self, song: Song = None) -> str:  # type: ignore[override]
        pk = song.pk if song else self.object.pk
        return reverse_lazy('music:song-detail', kwargs={'pk': pk})

    def _is_ajax(self) -> bool:
        return self.request.headers.get('Accept', '').startswith('application/json')

    def _error_response(self, form, message: str):
        if self._is_ajax():
            return JsonResponse({'status': 'error', 'message': message}, status=422)
        messages.error(self.request, message)
        return self.render_to_response(self.get_context_data(form=form))


class SongLibraryView(LoginRequiredMixin, ListView):
    model = Song
    template_name = 'music/song_list.html'
    context_object_name = 'songs'
    paginate_by = 20

    def get_queryset(self):
        service = SongLibraryService()
        query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip().upper()
        sort = self.request.GET.get('sort', 'newest')

        qs = service.search_songs(self.request.user, query)

        valid_statuses = {s.value for s in GenerationStatus}
        if status in valid_statuses:
            qs = qs.filter(generation_status=status)

        sort_map = {'newest': '-created_at', 'oldest': 'created_at', 'title': 'title'}
        return qs.order_by(sort_map.get(sort, '-created_at'))

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        service = SongLibraryService()
        ctx['stats'] = service.get_statistics(self.request.user)
        ctx['generation_statuses'] = GenerationStatus.choices
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_sort'] = self.request.GET.get('sort', 'newest')
        return ctx


class SongDetailView(LoginRequiredMixin, DetailView):
    model = Song
    template_name = 'music/song_detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Song, pk=self.kwargs['pk'], user=self.request.user)

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        song: Song = self.object
        ctx['is_completed'] = song.generation_status == GenerationStatus.COMPLETED
        ctx['is_generating'] = song.generation_status == GenerationStatus.GENERATING
        ctx['is_failed'] = song.generation_status == GenerationStatus.FAILED
        ctx['themes'] = song.themes.all()
        return ctx

    def post(self, request, *args, **kwargs):
        song = self.get_object()
        action = request.POST.get('action')
        service = SongLibraryService()

        if action == 'delete':
            service.delete_song(song.pk, request.user)
            messages.success(request, f'"{song.title}" has been deleted.')
            return redirect(reverse_lazy('music:song-library'))

        if action == 'share':
            service.share_song(song.pk, request.user)
            messages.success(request, f'"{song.title}" is now shared.')

        if action == 'unshare':
            service.unshare_song(song.pk, request.user)
            messages.info(request, f'"{song.title}" is no longer shared.')

        if action == 'regenerate':
            gen_service = SongGenerationService()
            form_data = {
                'title':        song.title,
                'singer_model': song.singer_model,
                'genre':        song.genre,
                'mood':         song.mood,
                'occasion':     song.occasion,
                'themes':       list(song.themes.all()),
                'duration':     song.duration,
                'review_notes': song.review_notes,
            }
            try:
                new_song = gen_service.generate_song(user=request.user, form_data=form_data)
                messages.success(request, f'"{new_song.title}" has been resubmitted for generation.')
                return redirect(reverse_lazy('music:song-detail', kwargs={'pk': new_song.pk}))
            except Exception:
                messages.error(request, 'Regeneration failed. Please try again.')

        return redirect(reverse_lazy('music:song-detail', kwargs={'pk': song.pk}))


class FeedbackView(LoginRequiredMixin, CreateView):
    model = Feedback
    fields = ['content']
    template_name = 'music/feedback.html'
    success_url = reverse_lazy('music:song-library')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Thank you for your feedback!')
        return super().form_valid(form)


class SongGenerationPreviewView(LoginRequiredMixin, View):
    template_name = 'music/song_preview.html'

    def _get_form_from_session(self, request):
        stored = request.session.get('song_preview_data')
        if not stored:
            return None, None
        qd = QueryDict('', mutable=True)
        for key, values in stored.items():
            qd.setlist(key, values)
        form = SongGenerationForm(data=qd)
        form.is_valid()
        return form, stored

    def get(self, request):
        form, stored = self._get_form_from_session(request)
        if form is None:
            return redirect(reverse_lazy('music:song-generate'))
        return render(request, self.template_name, {'form': form, 'preview': form.cleaned_data})

    def post(self, request):
        form, stored = self._get_form_from_session(request)
        if form is None:
            messages.error(request, 'Session expired. Please fill in the form again.')
            return redirect(reverse_lazy('music:song-generate'))

        if not form.is_valid():
            request.session.pop('song_preview_data', None)
            messages.error(request, 'Preview data was invalid. Please try again.')
            return redirect(reverse_lazy('music:song-generate'))

        service = SongGenerationService()
        try:
            song = service.generate_song(user=request.user, form_data=form.cleaned_data)
        except InvalidGenerationInput as exc:
            logger.warning('Invalid preview input from user %s: %s', request.user.pk, exc)
            messages.error(request, str(exc))
            return redirect(reverse_lazy('music:song-generate'))
        except SongGenerationError:
            logger.error('Generation error for user %s', request.user.pk)
            messages.error(request, 'Song generation failed. Please try again later.')
            return redirect(reverse_lazy('music:song-generate'))

        request.session.pop('song_preview_data', None)
        messages.success(request, f'"{song.title}" has been submitted for generation!')
        return redirect(reverse_lazy('music:song-detail', kwargs={'pk': song.pk}))


class SharedSongView(DetailView):
    model = Song
    template_name = 'music/shared_song.html'
    pk_url_kwarg = 'song_id'

    def get_object(self, queryset=None):
        return get_object_or_404(Song, pk=self.kwargs['song_id'], is_shared=True)

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx['themes'] = self.object.themes.all()
        return ctx


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


@login_required
def download_song(request, pk):
    song = get_object_or_404(Song, pk=pk, user=request.user)
    if not song.audio_url:
        messages.error(request, 'No audio file available for this song.')
        return redirect(reverse_lazy('music:song-detail', kwargs={'pk': pk}))
    return redirect(song.audio_url)
