import re

import requests as rlib
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ..models import Song


@login_required
def song_audio(request, pk):
    song = get_object_or_404(Song, pk=pk, user=request.user)
    if not song.audio_url:
        return HttpResponse(status=404)

    try:
        upstream = rlib.get(song.audio_url, timeout=30)
        upstream.raise_for_status()
    except rlib.exceptions.RequestException:
        return HttpResponse(status=502)

    content = upstream.content
    total = len(content)
    content_type = upstream.headers.get('Content-Type', 'audio/mpeg')

    range_header = request.META.get('HTTP_RANGE', '')
    if range_header:
        m = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else total - 1
            end = min(end, total - 1)
            chunk = content[start:end + 1]
            resp = HttpResponse(chunk, status=206, content_type=content_type)
            resp['Content-Range'] = f'bytes {start}-{end}/{total}'
            resp['Content-Length'] = str(len(chunk))
            resp['Accept-Ranges'] = 'bytes'
            return resp

    resp = HttpResponse(content, content_type=content_type)
    resp['Content-Length'] = str(total)
    resp['Accept-Ranges'] = 'bytes'
    return resp
