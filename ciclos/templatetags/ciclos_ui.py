from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


# A cor do status era decidida comparando string crua do banco dentro do
# template, em quatro arquivos. A decisão passa a acontecer num lugar só.
CORES_STATUS = {
    "em andamento": {
        "fundo": "bg-green-100", "texto": "text-green-700",
        "borda": "border-green-200", "ponto": "bg-green-500",
    },
    "finalizado": {
        "fundo": "bg-blue-50", "texto": "text-[#1a5b9e]",
        "borda": "border-blue-200", "ponto": "bg-[#1a5b9e]",
    },
    "arquivado": {
        "fundo": "bg-gray-100", "texto": "text-gray-500",
        "borda": "border-gray-200", "ponto": "bg-gray-400",
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
