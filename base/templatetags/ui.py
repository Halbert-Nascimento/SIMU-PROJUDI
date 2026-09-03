from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from base.ui import CLASSE_CAMPO, CLASSES_BOTAO
from usuarios.models import Usuario

register = template.Library()


@register.simple_tag
def classe_campo() -> str:
    """Classes do input/select padrão do sistema."""
    return CLASSE_CAMPO


@register.simple_tag
def classe_botao(variante: str = "primario") -> str:
    """
    Classes de cor e estado do botão. O padding fica no ponto de uso:
        class="{% classe_botao 'primario' %} py-1.5 px-6"
    """
    return CLASSES_BOTAO.get(variante, CLASSES_BOTAO["primario"])


# ---------------------------------------------------------------------------
# Componentes de bloco
# ---------------------------------------------------------------------------

@register.simple_block_tag
def card(content, titulo, icone="fa-folder-open", classe="", classe_corpo="", contador=None):
    """
    Painel padrão: moldura, cabeçalho navy com ícone e corpo livre.

        {% card titulo="Dados do Ciclo" icone="fa-folder-open" %}
            <form>...</form>
        {% endcard %}
    """
    return mark_safe(render_to_string(
        "base/components/_card.html",
        {
            "titulo": titulo,
            "icone": icone,
            "classe": classe,
            "classe_corpo": classe_corpo,
            "contador": contador,
            "corpo": content,
        },
    ))


@register.simple_block_tag
def modal(content, id, titulo, icone="fa-circle-info", tamanho="", fechar_onclick="", fechar_id=""):
    """
    Diálogo modal. `tamanho` aceita "sm" (540px), "" (580px) ou "lg" (720px).
    A abertura/fechamento continua a cargo do JS da tela, alternando a classe
    `open` no overlay — mesmo contrato que as telas já usavam. O botão de
    fechar sai com `fechar_onclick` (handler) ou `fechar_id` (listener).
    """
    return mark_safe(render_to_string(
        "base/components/_modal.html",
        {
            "id": id,
            "titulo": titulo,
            "icone": icone,
            "tamanho": tamanho,
            "fechar_onclick": fechar_onclick,
            "fechar_id": fechar_id,
            "corpo": content,
        },
    ))


@register.simple_block_tag
def campo(content, label, erros=None, ajuda=""):
    """
    Rótulo + controle + erro de validação. O controle é escrito no ponto de
    uso, então selects com opções montadas à mão continuam funcionando:

        {% campo label="Ano *" erros=form.ano.errors %}
            <input type="number" name="ano" class="{% classe_campo %}">
        {% endcampo %}
    """
    return mark_safe(render_to_string(
        "base/components/_campo.html",
        {"label": label, "erros": erros, "ajuda": ajuda, "controle": content},
    ))


# ---------------------------------------------------------------------------
# Componentes de domínio transversal
# ---------------------------------------------------------------------------

@register.inclusion_tag("base/components/_nav_secundaria.html", takes_context=True)
def nav_secundaria(context, voltar_url="", voltar_label=""):
    """
    Barra de navegação abaixo do cabeçalho. Os itens dependem do perfil, que
    antes era decidido por {% if %} copiado em cada template.
    """
    # mesmo usuário que base.html enxerga: o do context processor de auth
    user = context.get("user")
    if user is None:
        user = getattr(context.get("request"), "user", None)
    e_aluno = bool(
        user
        and user.is_authenticated
        and user.tipo_perfil_global == Usuario.TipoPerfilGlobal.ALUNO
    )
    return {
        "e_aluno": e_aluno,
        "user": user,
        "voltar_url": voltar_url,
        "voltar_label": voltar_label,
    }


@register.simple_tag
def icone_mensagem(tags: str) -> str:
    """Ícone FontAwesome correspondente ao nível da mensagem."""
    tags = tags or ""
    if "success" in tags:
        return mark_safe("fa-circle-check")
    if "error" in tags:
        return mark_safe("fa-circle-xmark")
    if "warning" in tags:
        return mark_safe("fa-triangle-exclamation")
    return mark_safe("fa-circle-info")
