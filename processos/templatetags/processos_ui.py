from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


# Mesma decisão de cor que estava replicada em três templates, comparando o
# nome do status vindo do banco.
CORES_STATUS = {
    "em andamento": {
        "fundo": "bg-green-100", "texto": "text-green-700",
        "borda": "border-green-200", "ponto": "bg-green-500", "pill": "ok",
    },
    "suspenso": {
        "fundo": "bg-yellow-100", "texto": "text-yellow-700",
        "borda": "border-yellow-200", "ponto": "bg-yellow-500", "pill": "warn",
    },
    "arquivado": {
        "fundo": "bg-gray-100", "texto": "text-gray-500",
        "borda": "border-gray-200", "ponto": "bg-gray-400", "pill": "gray",
    },
}

CORES_PADRAO = {
    "fundo": "bg-blue-50", "texto": "text-blue-700",
    "borda": "border-blue-200", "ponto": "bg-blue-500", "pill": "ok",
}


def _cores(status) -> dict:
    nome = (getattr(status, "nome_status", "") or "").lower()
    return CORES_STATUS.get(nome, CORES_PADRAO)


@register.simple_tag
def badge_status_processo(status):
    """Etiqueta preenchida do status do processo — usada no painel."""
    return mark_safe(render_to_string(
        "processos/components/_badge_status.html",
        {"status": status, "cores": _cores(status)},
    ))


@register.simple_tag
def pill_status_processo(status):
    """Versão compacta em `.pill`, usada nas telas processuais."""
    return mark_safe(render_to_string(
        "processos/components/_pill_status.html",
        {"status": status, "cores": _cores(status)},
    ))
