from __future__ import annotations

from django import template

from avaliacoes.estrelas import (
    ESTRELAS_MAX,
    ESTRELAS_MIN,
    contexto_estrelas,
    nota_para_estrelas,
)

register = template.Library()


@register.filter
def em_estrelas(nota):
    """Nota gravada (0–10) em estrelas inteiras: `{{ fb.nota|em_estrelas }}`."""
    return nota_para_estrelas(nota)


@register.inclusion_tag("avaliacoes/components/_estrelas.html")
def estrelas(valor, herda_cor=False):
    """
    Estrelas só de leitura. `valor` já em estrelas (use `|em_estrelas` sobre uma
    nota gravada). Com `herda_cor=True` as estrelas ficam na cor do elemento pai,
    como dentro de uma `.pill`. Valor nulo mostra um traço.
    """
    return contexto_estrelas(valor, herda_cor=herda_cor)


@register.inclusion_tag("avaliacoes/components/_estrelas_campo.html")
def estrelas_campo(nome, valor=None, id_prefixo="estrelas"):
    """
    Seletor de 1 a 5 estrelas (grupo de rádios). `valor` aceita o que o
    formulário devolver — inteiro do `initial` ou texto do POST —, e o que não
    for uma opção válida simplesmente não marca nenhuma.
    """
    try:
        marcada = int(valor)
    except (TypeError, ValueError):
        marcada = None
    # Do maior para o menor: o CSS inverte a linha e assim o preenchimento até a
    # estrela escolhida sai de um seletor de irmãos, sem JavaScript.
    opcoes = [
        {"valor": n, "id": f"{id_prefixo}-{n}", "marcada": n == marcada}
        for n in range(ESTRELAS_MAX, ESTRELAS_MIN - 1, -1)
    ]
    return {"nome": nome, "opcoes": opcoes, "maximo": ESTRELAS_MAX}
