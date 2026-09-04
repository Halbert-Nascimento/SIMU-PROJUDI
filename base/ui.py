"""
Cadeias de classe Tailwind compartilhadas entre templates e widgets de form.

Valores do Guia de Design (seções 04 e 05). Fica fora de templatetags/ para que
forms.py possa importar sem depender da camada de template.

O guia fixa: raio 0, borda de 1px sempre presente, rótulo em caixa alta com
letter-spacing .1em e peso 700. O padding fica no ponto de uso porque varia
entre botão padrão (8px 18px) e ação de linha (5px 10px).
"""
from __future__ import annotations

# `block` não é decoração: como caixa inline, o campo herda a caixa de linha do
# pai e sobra folga de descida embaixo dele — o que desalinha qualquer botão
# posto ao lado numa linha flex. Em bloco, a altura da linha é a do campo.
CLASSE_CAMPO = (
    "block w-full bg-white border border-campo-borda rounded-campo px-[9px] py-2 "
    "text-corpo text-texto placeholder:text-rotulo "
    "focus:outline-none focus:border-acao"
)

# Mesmo campo, para número CNJ, CPF/CNPJ, valor e demais dados codificados.
CLASSE_CAMPO_MONO = CLASSE_CAMPO + " font-mono"

# `btn` não pinta nada: é o marcador de "isto é botão, não link". `componentes.css`
# usa em `.tbl-projudi a:not(.btn)` — sem ele, o seletor de link de tabela (0-1-1)
# vence o `text-white` da variante (0-1-0) e repinta o rótulo de azul sobre navy.
CLASSES_BOTAO = {
    # Uma única ação principal por tela ou por barra.
    "primario": (
        "btn bg-navy hover:bg-acao text-white border border-navy hover:border-acao "
        "text-meta font-bold uppercase tracking-[.1em] transition-colors"
    ),
    # Apoio: limpar, cancelar, exportar.
    "secundario": (
        "btn bg-white hover:border-navy text-texto-neutro hover:text-navy "
        "border border-campo-borda "
        "text-meta font-bold uppercase tracking-[.1em] transition-colors"
    ),
    # Dentro de tabela — menor, para não engordar a linha.
    "linha": (
        "btn bg-white hover:bg-[#f2f6fd] text-acao border border-[#c9d5ea] hover:border-acao "
        "text-micro font-bold uppercase tracking-[.07em] transition-colors"
    ),
    # Nunca vermelho sólido; a confirmação vem no modal.
    "destrutivo": (
        "btn bg-white hover:bg-erro-bg text-erro-txt border border-erro-bd hover:border-erro-txt "
        "text-meta font-bold uppercase tracking-[.1em] transition-colors"
    ),
    # Guia seção 04: sem opacidade global — fundo, texto e cursor próprios.
    "desabilitado": (
        "btn bg-neutro-bg text-desabilitado border border-neutro-bd cursor-not-allowed "
        "text-meta font-bold uppercase tracking-[.1em]"
    ),
    # Sobre o navy do cabeçalho.
    "sobre-navy": (
        "btn bg-transparent border border-white/25 hover:border-marca "
        "text-[#d8dae9] hover:text-white "
        "text-micro font-bold uppercase tracking-[.08em] transition-colors"
    ),
}

# Padding padrão de cada variante, para quem não quiser definir no ponto de uso.
PADDING_BOTAO = {
    "primario":   "px-[18px] py-2",
    "secundario": "px-4 py-2",
    "linha":      "px-2.5 py-[5px]",
    "destrutivo": "px-4 py-2",
    "desabilitado": "px-4 py-2",
    "sobre-navy": "px-2.5 py-[5px]",
}
