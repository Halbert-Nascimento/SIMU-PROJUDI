from django import template

from ..capitulos import NOME_DO_PAPEL

register = template.Library()


@register.filter
def nome_do_papel(cod):
    """Termo por extenso da sigla do cargo, para o hover do quadradinho."""
    return NOME_DO_PAPEL.get(cod, cod)
