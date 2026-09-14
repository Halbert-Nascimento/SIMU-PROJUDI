from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from ..models import CategoriaEfeitoColateral

register = template.Library()

# Ícone + frase por categoria (8.4) — indicador genérico do Ponto 6, sem cálculo de data/agenda.
INDICADOR_EFEITO_COLATERAL = {
    CategoriaEfeitoColateral.ABRE_PRAZO: ("fa-clock", "abre um prazo"),
    CategoriaEfeitoColateral.ENCERRA_PRAZO: ("fa-clock", "encerra um prazo"),
    CategoriaEfeitoColateral.REABRE_PRAZO: ("fa-clock", "reabre um prazo"),
    CategoriaEfeitoColateral.AGENDA_AUDIENCIA: ("fa-calendar-days", "agenda uma audiência"),
    CategoriaEfeitoColateral.NOTIFICA: ("fa-bell", "notifica as partes"),
}


@register.simple_tag
def badges_efeito_colateral(categorias):
    """Indicadores genéricos do Ponto 6 — um badge `.pill warn` por categoria cadastrada no tipo."""
    badges = [
        {"icone": INDICADOR_EFEITO_COLATERAL[c][0], "descricao": INDICADOR_EFEITO_COLATERAL[c][1]}
        for c in categorias
    ]
    return mark_safe(render_to_string(
        "movimentacoes/components/_badges_efeito_colateral.html",
        {"badges": badges},
    ))
