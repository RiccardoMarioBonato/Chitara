"""
Root URL configuration for the Chitara project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='music/home.html'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('songs/', include('music.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
