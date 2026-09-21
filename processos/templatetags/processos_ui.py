from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


# Mesma decisão de cor que estava replicada em três templates, comparando o
# nome do status vindo do banco.
CORES_STATUS = {
    "em andamento": {
        "fundo": "bg-ok-bg", "texto": "text-ok-txt",
        "borda": "border-ok-bd", "ponto": "bg-ok-txt", "pill": "ok",
    },
    "suspenso": {
        "fundo": "bg-atencao-bg", "texto": "text-atencao-txt",
        "borda": "border-atencao-bd", "ponto": "bg-atencao-txt", "pill": "warn",
    },
    "arquivado": {
        "fundo": "bg-neutro-bg", "texto": "text-neutro-txt",
        "borda": "border-neutro-bd", "ponto": "bg-neutro-txt", "pill": "gray",
    },
}

CORES_PADRAO = {
    "fundo": "bg-neutro-bg", "texto": "text-navy",
    "borda": "border-neutro-bd", "ponto": "bg-navy", "pill": "ok",
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
