from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from ..models import GenerationStatus, Song
from ..services import SongLibraryService


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
