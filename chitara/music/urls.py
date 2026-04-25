"""
URL Configuration — music/urls.py

Include in the project's root urls.py with:
    path('songs/', include('music.urls', namespace='music')),
"""

from django.urls import path

from .views import (
    FeedbackView,
    SharedSongView,
    SongDetailView,
    SongGenerationPreviewView,
    SongGenerationView,
    SongLibraryView,
    SunoCallbackView,
    download_song,
    get_song_status,
)

app_name = 'music'

urlpatterns = [
    path('generate/',                              SongGenerationView.as_view(),        name='song-generate'),
    path('generate/preview/',                      SongGenerationPreviewView.as_view(), name='song-preview'),
    path('',                                       SongLibraryView.as_view(),           name='song-library'),
    path('<int:pk>/',                              SongDetailView.as_view(),            name='song-detail'),
    path('feedback/',                              FeedbackView.as_view(),              name='feedback'),
    path('shared/<int:song_id>/',                  SharedSongView.as_view(),            name='shared-song'),
    path('api/callback/',                          SunoCallbackView.as_view(),          name='suno-callback'),
    path('generation/status/<int:song_id>/',       get_song_status,                     name='song-status'),
    path('<int:pk>/download/',                     download_song,                       name='song-download'),
]
