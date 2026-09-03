"""
Storage de arquivos estáticos que carimba a URL com a versão do arquivo.

O runserver serve /static/ apenas com Last-Modified — sem Cache-Control e sem
ETag. Nesse cenário o navegador decide sozinho reusar a cópia que já tem, e uma
alteração no tema ou no CSS pode simplesmente não chegar na tela. Anexar
?v=<mtime> faz a URL mudar junto com o arquivo, então o cache antigo nunca casa.
"""
from __future__ import annotations

import os

from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage


class StaticFilesVersionados(StaticFilesStorage):
    """Mesmo storage padrão, com ?v=<mtime> em toda URL resolvida por {% static %}."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._versoes: dict[str, str] = {}

    def url(self, name):
        url = super().url(name)
        versao = self._versao(name)
        if not versao:
            return url
        separador = "&" if "?" in url else "?"
        return f"{url}{separador}v={versao}"

    def _versao(self, name: str) -> str:
        # Fora de DEBUG o arquivo não muda enquanto o processo vive; em DEBUG o
        # mtime é relido a cada render, que é o que faz a edição aparecer no F5.
        if not settings.DEBUG and name in self._versoes:
            return self._versoes[name]

        caminho = self._caminho_no_disco(name)
        try:
            versao = str(int(os.path.getmtime(caminho))) if caminho else ""
        except OSError:
            versao = ""

        if not settings.DEBUG:
            self._versoes[name] = versao
        return versao

    def _caminho_no_disco(self, name: str) -> str | None:
        # Em DEBUG o arquivo ainda está em STATICFILES_DIRS (não houve
        # collectstatic); em produção já foi copiado para STATIC_ROOT.
        if settings.DEBUG:
            from django.contrib.staticfiles import finders

            return finders.find(name)

        try:
            caminho = self.path(name)
        except (NotImplementedError, ValueError):
            return None
        return caminho if os.path.exists(caminho) else None
