import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from ..forms import SongGenerationForm
from ..models import Genre, Mood, Occasion, Song, Theme

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
