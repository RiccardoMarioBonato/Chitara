import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView

from ..models import GenerationStatus, Song
from ..services import SongGenerationService, SongLibraryService

logger = logging.getLogger(__name__)


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


@login_required
def download_song(request, pk):
    song = get_object_or_404(Song, pk=pk, user=request.user)
    if not song.audio_url:
        messages.error(request, 'No audio file available for this song.')
        return redirect(reverse_lazy('music:song-detail', kwargs={'pk': pk}))
    return redirect(song.audio_url)
