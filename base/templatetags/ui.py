from __future__ import annotations

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from base.ui import CLASSE_CAMPO, CLASSE_CAMPO_MONO, CLASSES_BOTAO, PADDING_BOTAO
from usuarios.models import Usuario

register = template.Library()


@register.simple_tag
def classe_campo(mono: bool = False) -> str:
    """
    Classes do input/select padrão. Use mono=True em número CNJ, CPF/CNPJ,
    valor da causa e demais dados codificados, como o guia exige.
    """
    return CLASSE_CAMPO_MONO if mono else CLASSE_CAMPO


@register.simple_tag
def classe_botao(variante: str = "primario", padding: bool = False) -> str:
    """
    Cor e estado do botão. Com padding=True sai também o espaçamento do guia:
        class="{% classe_botao 'primario' padding=True %}"
    """
    classes = CLASSES_BOTAO.get(variante, CLASSES_BOTAO["primario"])
    if padding:
        classes += " " + PADDING_BOTAO.get(variante, PADDING_BOTAO["primario"])
    return classes


@register.simple_tag
def padding_botao(variante: str = "primario") -> str:
    """Só o espaçamento da variante — para quem já tem a cadeia de cor."""
    return PADDING_BOTAO.get(variante, PADDING_BOTAO["primario"])


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
def campo(content, label, erros=None, ajuda="", para=""):
    """
    Rótulo + controle + erro de validação. O controle é escrito no ponto de
    uso, então selects com opções montadas à mão continuam funcionando:

        {% campo label="Ano *" erros=form.ano.errors %}
            <input type="number" name="ano" class="{% classe_campo %}">
        {% endcampo %}

    `para` amarra o <label> ao controle — passe field.id_for_label quando o
    campo vier de um form do Django. Todos os erros da lista são exibidos.
    """
    return mark_safe(render_to_string(
        "base/components/_campo.html",
        {"label": label, "erros": erros, "ajuda": ajuda,
         "para": para, "controle": content},
    ))


# ---------------------------------------------------------------------------
# Componentes de domínio transversal
# ---------------------------------------------------------------------------

@register.inclusion_tag("base/components/_nav_secundaria.html", takes_context=True)
def nav_secundaria(context, ativo="", voltar_url="", voltar_label=""):
    """
    Barra de navegação abaixo do cabeçalho. Os itens dependem do perfil, e
    `ativo` marca a aba corrente com o sublinhado do guia — aceita
    "inicio", "processos", "audiencias" ou "notas".
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
        "ativo": ativo,
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
