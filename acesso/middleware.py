from __future__ import annotations

import time

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class SessionActivityMiddleware:
    """
    Expira a sessão depois de `SESSION_COOKIE_AGE` segundos sem atividade.

    Atividade é toda requisição que partiu de uma ação do usuário. Requisição
    que o navegador dispara sozinho não conta: o sino consulta a contagem de
    notificações de 30 em 30 segundos, e enquanto isso valia como atividade a
    sessão abandonada nunca expirava — bastava a aba ficar aberta.
    """

    # Rotas automáticas, sem ninguém na frente da tela quando acontecem.
    # Guardadas por nome e traduzidas para caminho, para que mudar a URL não
    # abra um buraco silencioso na regra.
    ROTAS_AUTOMATICAS = ("notificacoes:contagem",)

    def __init__(self, get_response):
        self.get_response = get_response
        self._caminhos_automaticos = None

    @property
    def caminhos_automaticos(self) -> frozenset[str]:
        # resolvido no primeiro uso: no __init__ a URLConf ainda pode não estar carregada
        if self._caminhos_automaticos is None:
            self._caminhos_automaticos = frozenset(
                reverse(rota) for rota in self.ROTAS_AUTOMATICAS
            )
        return self._caminhos_automaticos

    def __call__(self, request):
        if request.user.is_authenticated:
            now     = time.time()
            last    = request.session.get('last_activity')
            timeout = settings.SESSION_COOKIE_AGE

            if last and (now - last) > timeout:
                request.session.flush()
                return redirect(f"{reverse('acesso:login')}?exp=1")

            if request.path not in self.caminhos_automaticos:
                request.session['last_activity'] = now

        return self.get_response(request)
