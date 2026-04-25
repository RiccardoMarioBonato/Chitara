from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from ..models import Song


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
