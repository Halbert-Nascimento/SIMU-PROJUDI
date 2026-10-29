"""Registro dos capítulos do manual; sem import de Django para o gerador usar o mesmo arquivo."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capitulo:
    slug: str
    titulo: str
    grupo: str
    icone: str
    resumo: str
    # títulos H2 do MANUAL_DO_USUARIO.md que compõem a página; vazio = página gerada pelo sistema
    secoes: tuple[str, ...] = ()


GRUPO_INICIO = "Comece por aqui"
GRUPO_PERFIS = "Perfis do sistema"
GRUPO_PAPEIS = "Papéis no processo"
GRUPO_REFERENCIA = "Referência"

CAPITULOS: tuple[Capitulo, ...] = (
    Capitulo(
        "guia-geral", "Guia geral", GRUPO_INICIO, "fa-book",
        "O que é o simulador, como ciclos, grupos e papéis se encaixam e como funcionam os prazos.",
        ("Declaração de Uso", "Introdução", "Guia Geral do Simulador"),
    ),
    Capitulo(
        "primeiros-passos", "Primeiros passos", GRUPO_INICIO, "fa-door-open",
        "Cadastro, liberação do acesso, login, redirecionamento por perfil e troca de senha.",
        ("Primeiros Passos",),
    ),
    Capitulo(
        "admin", "Admin", GRUPO_PERFIS, "fa-user-shield",
        "Painel de controle, aprovação de cadastros, ciclos de simulação e grupos de trabalho.",
        ("Capítulo do Admin",),
    ),
    Capitulo(
        "coordenador", "Coordenador", GRUPO_PERFIS, "fa-user-tie",
        "O que o Coordenador vê e faz no sistema.",
        ("Capítulo do Coordenador",),
    ),
    Capitulo(
        "professor", "Professor", GRUPO_PERFIS, "fa-chalkboard-user",
        "Painel, vínculo de alunos a grupos, avaliação de movimentações e bloqueio de cadastros.",
        ("Capítulo do Professor",),
    ),
    Capitulo(
        "aluno", "Aluno", GRUPO_PERFIS, "fa-user-graduate",
        "Área do aluno, cadastro de processo, movimentação, documentos, editor on-line e notas.",
        ("Capítulo do Aluno",),
    ),
    Capitulo(
        "serventia-cartorio", "Serventia / Cartório (SC)", GRUPO_PAPEIS, "fa-box-archive",
        "Faz o processo andar: autua, cita, publica, certifica e arquiva.",
        ("Capítulo de Serventia/Cartório (SC)",),
    ),
    Capitulo(
        "advogados-polo-ativo", "Advogados — Polo Ativo (APA)", GRUPO_PAPEIS, "fa-file-arrow-up",
        "Abre a ação, responde à emenda e acompanha o processo até o recurso.",
        ("Capítulo de Advogados Polo Ativo (APA)",),
    ),
    Capitulo(
        "advogados-polo-passivo", "Advogados — Polo Passivo (APP)", GRUPO_PAPEIS, "fa-shield-halved",
        "Apresenta a contestação e acompanha o processo até o recurso.",
        ("Capítulo de Advogados Polo Passivo (APP)",),
    ),
    Capitulo(
        "ministerio-publico", "Ministério Público (MP)", GRUPO_PAPEIS, "fa-file-circle-check",
        "Manifesta-se como fiscal da lei quando o Juiz determina.",
        ("Capítulo do Ministério Público (MP)",),
    ),
    Capitulo(
        "juiz", "Juiz (JZ)", GRUPO_PAPEIS, "fa-scale-balanced",
        "Despacha, concilia, saneia e sentencia.",
        ("Capítulo do Juiz (JZ)",),
    ),
    Capitulo(
        "notificacoes", "Notificações do sistema", GRUPO_REFERENCIA, "fa-bell",
        "Como o sino de notificações funciona para cada perfil.",
        ("Notificações do Sistema",),
    ),
    Capitulo(
        "linha-do-processo", "Linha do processo", GRUPO_REFERENCIA, "fa-timeline",
        "Todos os atos do processo, em ordem, com quem pratica cada um e quando fica disponível.",
    ),
    Capitulo(
        "glossario", "Glossário", GRUPO_REFERENCIA, "fa-spell-check",
        "Siglas e abreviações usadas no simulador.",
        ("Glossário de Abreviações e Siglas",),
    ),
)

POR_SLUG = {capitulo.slug: capitulo for capitulo in CAPITULOS}

SLUG_LINHA_DO_PROCESSO = "linha-do-processo"

NOME_DO_PAPEL = {
    "SC": "Serventia/Cartório",
    "APA": "Advogados Polo Ativo",
    "APP": "Advogados Polo Passivo",
    "MP": "Ministério Público",
    "JZ": "Juiz",
}

# capítulos de papel: o fim da página recebe a tabela de atos daquele cargo, lida do catálogo
CARGO_DO_CAPITULO = {
    "serventia-cartorio": ("SC", "Serventia/Cartório (SC)"),
    "advogados-polo-ativo": ("APA", "Advogados Polo Ativo (APA)"),
    "advogados-polo-passivo": ("APP", "Advogados Polo Passivo (APP)"),
    "ministerio-publico": ("MP", "Ministério Público (MP)"),
    "juiz": ("JZ", "Juiz (JZ)"),
}
