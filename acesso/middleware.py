from __future__ import annotations

import time

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class SessionActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now     = time.time()
            last    = request.session.get('last_activity')
            timeout = settings.SESSION_COOKIE_AGE

            if last and (now - last) > timeout:
                request.session.flush()
                return redirect(f"{reverse('acesso:login')}?exp=1")

            request.session['last_activity'] = now

        return self.get_response(request)
