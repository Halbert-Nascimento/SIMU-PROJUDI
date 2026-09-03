from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


# A cor do status era decidida comparando string crua do banco dentro do
# template, em quatro arquivos. A decisão passa a acontecer num lugar só.
CORES_STATUS = {
    "em andamento": {
        "fundo": "bg-ok-bg", "texto": "text-ok-txt",
        "borda": "border-ok-bd", "ponto": "bg-ok-txt",
    },
    "finalizado": {
        "fundo": "bg-neutro-bg", "texto": "text-navy",
        "borda": "border-neutro-bd", "ponto": "bg-navy",
    },
    "arquivado": {
        "fundo": "bg-neutro-bg", "texto": "text-neutro-txt",
        "borda": "border-neutro-bd", "ponto": "bg-neutro-txt",
    },
}

CORES_PADRAO = CORES_STATUS["arquivado"]


def _cores(status) -> dict:
    nome = (getattr(status, "nome_status", "") or "").lower()
    return CORES_STATUS.get(nome, CORES_PADRAO)


@register.simple_tag
def badge_status_ciclo(status):
    """Etiqueta preenchida com o status do ciclo — usada em listagens."""
    return mark_safe(render_to_string(
        "ciclos/components/_badge_status.html",
        {"status": status, "cores": _cores(status)},
    ))


@register.simple_tag
def ponto_status_ciclo(status):
    """Versão discreta: bolinha colorida + nome do status, para subtítulos."""
    return mark_safe(render_to_string(
        "ciclos/components/_ponto_status.html",
        {"status": status, "cores": _cores(status)},
    ))
