from __future__ import annotations

import time

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from usuarios.models import VERSAO_TERMOS_ATUAL


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


class TermosAceitosMiddleware:
    """
    Prende no portão `acesso:aceite_termos_pendente` quem está autenticado mas
    não aceitou a versão vigente dos Termos de Uso / Política de Privacidade.

    Cobre tanto quem nunca aceitou (conta criada por `createsuperuser`, ou
    qualquer conta que existia antes deste recurso) quanto quem aceitou uma
    versão antiga — os dois casos caem aqui porque a comparação é sempre
    contra `VERSAO_TERMOS_ATUAL`, não contra "aceitou alguma vez".

    Mesmo desenho do `SessionActivityMiddleware` logo acima, não do
    `ciclos.middleware.AlunoSemCicloMiddleware`: a decisão é em `__call__`,
    antes de chamar `self.get_response`, com as rotas liberadas resolvidas
    para caminho via `reverse()` (não prefixo de caminho, então mudar uma URL
    não abre um buraco silencioso na regra — mesma garantia de checar por
    nome de rota, só que resolvida aqui em vez de em `resolver_match`).
    Decidir em `process_view` chegaria tarde demais: todo middleware listado
    depois deste em `MIDDLEWARE` (o `CicloAtivoMiddleware`, com sua consulta
    ao banco) já teria rodado antes de qualquer hook `process_view` disparar,
    então o redirect aconteceria só depois do trabalho descartado.
    """

    ROTAS_LIBERADAS = (
        "acesso:aceite_termos_pendente",
        "acesso:termos_de_uso",
        "acesso:politica_privacidade",
        "acesso:logout",
        # pings em segundo plano — a página de aceite mantém o cabeçalho
        # inteiro (inclusive o sino), que continua consultando essas rotas
        # a cada 30s; sem a liberação, cada consulta vira um redirect para
        # a própria página de aceite em vez de devolver o JSON esperado.
        "acesso:manter_sessao",
        "notificacoes:contagem",
        "notificacoes:recentes",
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self._caminhos_liberados = None

    @property
    def caminhos_liberados(self) -> frozenset[str]:
        if self._caminhos_liberados is None:
            self._caminhos_liberados = frozenset(
                reverse(rota) for rota in self.ROTAS_LIBERADAS
            )
        return self._caminhos_liberados

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.versao_termos_aceita != VERSAO_TERMOS_ATUAL
            and request.path not in self.caminhos_liberados
        ):
            destino = reverse("acesso:aceite_termos_pendente")
            return redirect(f"{destino}?{urlencode({'next': request.path})}")

        return self.get_response(request)
