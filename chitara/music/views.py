"""
Controller Layer — views.py
Thin layer: validates via forms, delegates to services, renders responses.
No ORM queries or business logic live here.
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .forms import SongGenerationForm
from .models import Feedback, GenerationStatus, Genre, Mood, Occasion, Song, Theme
from .services import (
    InvalidGenerationInput,
    SongGenerationError,
    SongGenerationService,
    SongLibraryService,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Song Generation View
# ---------------------------------------------------------------------------

class SongGenerationView(LoginRequiredMixin, CreateView):
    """
    GET  /music/generate/  — render the generation form.
    POST /music/generate/  — validate, call service, redirect or return JSON.

    AJAX: if request has Accept: application/json, returns JSON responses
    so the frontend can show a loading spinner without a full page reload.
    """

    model         = Song
    form_class    = SongGenerationForm
    template_name = 'music/song_form.html'

    def get_context_data(self, **kwargs) -> dict:
        """Populate dropdowns so the template doesn't query the DB itself."""
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'genres':    Genre.objects.all(),
            'moods':     Mood.objects.all(),
            'occasions': Occasion.objects.all(),
            'themes':    Theme.objects.all(),
        })
        return ctx

    def form_valid(self, form):
        """Hand validated data to the service; never save the model directly."""
        service = SongGenerationService()

        try:
            song = service.generate_song(
                user      = self.request.user,
                form_data = form.cleaned_data,
            )
        except InvalidGenerationInput as exc:
            logger.warning('Invalid input from user %s: %s', self.request.user.pk, exc)
            return self._error_response(form, str(exc))
        except SongGenerationError as exc:
            logger.error('Generation error for user %s: %s', self.request.user.pk, exc)
            return self._error_response(
                form,
                'Song generation failed. Please try again later.',
            )

        messages.success(
            self.request,
            f'"{song.title}" has been submitted for generation!',
        )

        if self._is_ajax():
            return JsonResponse({
                'status':   'ok',
                'song_id':  song.pk,
                'redirect': str(self.get_success_url(song)),
            })

        return redirect(self.get_success_url(song))

    def form_invalid(self, form):
        if self._is_ajax():
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        return super().form_invalid(form)

    def get_success_url(self, song: Song = None) -> str:  # type: ignore[override]
        pk = song.pk if song else self.object.pk
        return reverse_lazy('music:song-detail', kwargs={'pk': pk})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_ajax(self) -> bool:
        return self.request.headers.get('Accept', '').startswith('application/json')

    def _error_response(self, form, message: str):
        if self._is_ajax():
            return JsonResponse({'status': 'error', 'message': message}, status=422)
        messages.error(self.request, message)
        return self.render_to_response(self.get_context_data(form=form))


# ---------------------------------------------------------------------------
# Song Library View
# ---------------------------------------------------------------------------

class SongLibraryView(LoginRequiredMixin, ListView):
    """
    GET /music/library/  — paginated list of the user's songs.

    Supports:
        ?q=<search>          — filter by title
        ?status=<status>     — filter by generation status
        ?sort=newest|oldest|title
    """

    model         = Song
    template_name = 'music/song_list.html'
    context_object_name = 'songs'
    paginate_by   = 20

    def get_queryset(self):
        service = SongLibraryService()
        query  = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip().upper()
        sort   = self.request.GET.get('sort', 'newest')

        qs = service.search_songs(self.request.user, query)

        # Status filter
        valid_statuses = {s.value for s in GenerationStatus}
        if status in valid_statuses:
            qs = qs.filter(generation_status=status)

        # Sort
        sort_map = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'title':  'title',
        }
        qs = qs.order_by(sort_map.get(sort, '-created_at'))

        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)

        service = SongLibraryService()
        ctx['stats']            = service.get_statistics(self.request.user)
        ctx['generation_statuses'] = GenerationStatus.choices
        ctx['current_q']        = self.request.GET.get('q', '')
        ctx['current_status']   = self.request.GET.get('status', '')
        ctx['current_sort']     = self.request.GET.get('sort', 'newest')
        return ctx


# ---------------------------------------------------------------------------
# Song Detail View
# ---------------------------------------------------------------------------

class SongDetailView(LoginRequiredMixin, DetailView):
    """
    GET /music/songs/<pk>/  — full song detail page.

    Ownership is enforced: a user can only view their own songs
    (returns 404 for songs belonging to other users).
    """

    model         = Song
    template_name = 'music/song_detail.html'

    def get_object(self, queryset=None):
        """
        Return the Song only if it belongs to the logged-in user.
        Uses get_object_or_404 so non-owners get a 404, not a 403.
        """
        return get_object_or_404(
            Song,
            pk   = self.kwargs['pk'],
            user = self.request.user,
        )

    def get_context_data(self, **kwargs) -> dict:
        ctx  = super().get_context_data(**kwargs)
        song: Song = self.object

        ctx['is_completed']  = song.generation_status == GenerationStatus.COMPLETED
        ctx['is_generating'] = song.generation_status == GenerationStatus.GENERATING
        ctx['is_failed']     = song.generation_status == GenerationStatus.FAILED
        ctx['themes']        = song.themes.all()

        return ctx

    def post(self, request, *args, **kwargs):
        """
        Handle in-page actions (share / unshare / delete) via POST with
        an 'action' field, to avoid a separate URL for each operation.
        """
        song    = self.get_object()
        action  = request.POST.get('action')
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

        return redirect(reverse_lazy('music:song-detail', kwargs={'pk': song.pk}))


# ---------------------------------------------------------------------------
# Feedback View (bonus)
# ---------------------------------------------------------------------------

class FeedbackView(LoginRequiredMixin, CreateView):
    """
    GET  /music/feedback/  — render feedback form.
    POST /music/feedback/  — save feedback attributed to logged-in user.
    """

    model         = Feedback
    fields        = ['content']
    template_name = 'music/feedback.html'
    success_url   = reverse_lazy('music:song-library')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Thank you for your feedback!')
        return super().form_valid(form)

@method_decorator(csrf_exempt, name='dispatch')
class SunoCallbackView(View):
    """Handle SUNO webhook callbacks"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            print(f"📩 SUNO Callback received: {data}")
            
            # SUNO sends back the generation data
            task_id = data.get('task_id') or data.get('id')
            audio_url = data.get('audio_url', '')
            
            # Find and update the song
            if task_id:
                song = Song.objects.filter(external_id=task_id).first()
                if song:
                    song.audio_url = audio_url
                    song.generation_status = GenerationStatus.COMPLETED
                    song.save(update_fields=['audio_url', 'generation_status'])
                    logger.info('✅ Song %s updated via callback (task_id=%s)', song.id, task_id)
                else:
                    logger.warning('⚠️  No song found with external_id=%s', task_id)
            
            return JsonResponse({'status': 'received'})
        
        except Exception as e:
            print(f"❌ Callback error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)