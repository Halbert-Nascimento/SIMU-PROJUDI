from __future__ import annotations

from django.conf import settings


def session_timeout(request):
    return {"session_timeout_seconds": settings.SESSION_COOKIE_AGE}
