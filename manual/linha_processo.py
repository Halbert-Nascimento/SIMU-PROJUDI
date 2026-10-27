"""Linha do processo: o catálogo de movimentações lido do banco, na ordem do fluxo."""
from __future__ import annotations

from dataclasses import dataclass, field

from movimentacoes.catalogo import NOME_PROTOCOLO, NOME_REDISTRIBUICAO, NOMES_TRANSVERSAIS
from movimentacoes.models import TipoMovimentacao

# O banco não guarda fase nem ordem; esta é a sequência do fluxo, e o teste do app confere
# que nenhum tipo do catálogo fica de fora dela.
FASES = (
    ('Análise da inicial', (
        'Protocolo da Petição Inicial',
        'Autuação e Distribuição',
        'Custas Recolhidas',
        'Custas Não Recolhidas',
        'Intima autor p/ custas',
        'Custas Pagas Após Intimação',
        'Custas Não Pagas Após Intimação',
        'Cancelamento da Distribuição',
        'Conclusão ao Juiz',
        'Análise da Inicial — Irregular',
        'Análise da Inicial — Urgente',
        'Análise da Inicial — Indefere',
        'Análise da Inicial — Em Ordem',
        'Emenda da Inicial',
        'Emenda Apresentada',
        'Emenda Não Apresentada',
        'Indeferimento da Inicial',
        'Tutela de Urgência Deferida',
        'Tutela de Urgência Indeferida',
        'Liminar Concedida',
    )),
    ('Citação', (
        'Despacho de Citação',
        'Modalidade de Citação — Mandado',
        'Modalidade de Citação — Postal',
        'Modalidade de Citação — Edital',
        'Modalidade de Citação — Eletrônica',
        'Citação por Mandado',
        'Citação por Carta Postal (AR)',
        'Citação por Edital',
        'Citação Eletrônica/Portal',
        'Cumprimento do Mandado — Réu Encontrado',
        'Cumprimento do Mandado — Réu Não Encontrado',
        'Citação Positiva',
        'Citação Negativa',
        'Nova Modalidade — Edital',
        'Nova Modalidade — Repetir Mandado',
        'AR Assinado Juntado',
        'AR Não Assinado ou Não Devolvido',
        'Audiência de Conciliação — Com Acordo',
        'Audiência de Conciliação — Sem Acordo',
    )),
    ('Defesa', (
        'Contestação',
        'Revelia',
        'Efeitos da Revelia — Produz Efeitos',
        'Efeitos da Revelia — Sem Efeito',
        'Julgamento Antecipado',
        'Réplica do Autor',
        'MP Deve Intervir — Sim',
        'MP Deve Intervir — Não',
        'Manifestação do MP',
    )),
    ('Instrução', (
        'Decisão Saneadora',
        'Provas a Produzir — Perícia',
        'Provas a Produzir — Prova Oral',
        'Provas a Produzir — Só Documental',
        'Prova Pericial',
        'Laudo Pericial juntado',
        'Audiência de Instrução e Julgamento',
        'Resultado da Audiência — Acordo',
        'Resultado da Audiência — Memoriais',
        'Resultado da Audiência — Julgamento na Data',
        'Acordo em Audiência',
        'Memoriais/Alegações Finais',
    )),
    ('Sentença', (
        'Sentença Homologatória de Acordo',
        'Sentença',
        'Tipo de Sentença — Com Mérito',
        'Tipo de Sentença — Sem Mérito',
        'Com resolução do mérito',
        'Sem resolução do mérito',
    )),
    ('Recurso', (
        'Publicação/Intimação das Partes',
        'Embargos de Declaração',
        'Decisão nos Embargos',
        'Apelação',
        'Contrarrazões',
        'Remessa ao 2º Grau',
        'Julgamento pelo Tribunal',
        'Recurso Provido',
        'Recurso Não Provido',
        'Provimento Parcial',
        'Recurso Não Conhecido',
        'Baixa dos Autos ao 1º Grau',
        'Recurso Superior? (STJ/STF)',
        'REsp/RE (STJ/STF)',
    )),
    ('Trânsito em julgado', (
        'Trânsito em Julgado',
        'Certidão de Trânsito em Julgado',
        'Arquivamento',
    )),
)

FASE_TRANSVERSAIS = "A qualquer momento"
ORDEM_DOS_PAPEIS = ("SC", "APA", "APP", "MP", "JZ")


@dataclass
class Ato:
    numero: int
    nome: str
    papeis: list[str]
    depende_de: list[str]
    status: str
    efeitos: list[str]
    disponivel: bool
    observacao: str = ""
    libera: list[tuple[str, list[str]]] = field(default_factory=list)


@dataclass
class Fase:
    nome: str
    atos: list[Ato] = field(default_factory=list)


def _papeis_em_ordem(tipo) -> list[str]:
    return sorted(
        (c.cod for c in tipo.papeis_autorizados.all()),
        key=lambda cod: ORDEM_DOS_PAPEIS.index(cod) if cod in ORDEM_DOS_PAPEIS else len(ORDEM_DOS_PAPEIS),
    )


def _ato(tipo, numero):
    papeis = _papeis_em_ordem(tipo)
    observacao = ""
    disponivel = bool(papeis)
    if tipo.nome_movimentacao == NOME_PROTOCOLO:
        disponivel, observacao = True, "Registrado pela tela Cadastrar Processo."
    elif tipo.nome_movimentacao == NOME_REDISTRIBUICAO:
        disponivel, observacao = True, "Registrado pela tela de vínculo de grupos ao processo."
    elif not papeis:
        observacao = "Etapa futura do simulador: ainda não há quem pratique este ato."
    libera = sorted(
        (seguinte.nome_movimentacao, _papeis_em_ordem(seguinte))
        for seguinte in tipo.habilita_estes.all()
    )
    return Ato(
        numero=numero,
        nome=tipo.nome_movimentacao,
        papeis=papeis,
        depende_de=sorted(p.nome_movimentacao for p in tipo.precondicoes.all()),
        status=tipo.efeito_status.nome_status if tipo.efeito_status_id else "",
        efeitos=[e.categoria for e in tipo.efeitos_colaterais.all()],
        disponivel=disponivel,
        observacao=observacao,
        libera=libera,
    )


def montar_linha_do_processo() -> list[Fase]:
    """Fases em ordem, com os atos de cada uma; tipos novos do catálogo caem em "Outros atos"."""
    por_nome = {
        t.nome_movimentacao: t
        for t in TipoMovimentacao.objects.select_related("efeito_status").prefetch_related(
            "papeis_autorizados", "precondicoes", "efeitos_colaterais",
            "habilita_estes__papeis_autorizados",
        )
    }
    usados: set[str] = set()
    fases: list[Fase] = []
    numero = 0
    for nome_fase, nomes in FASES:
        fase = Fase(nome_fase)
        for nome in nomes:
            if nome in por_nome:
                numero += 1
                fase.atos.append(_ato(por_nome[nome], numero))
                usados.add(nome)
        fases.append(fase)

    transversais = Fase(FASE_TRANSVERSAIS)
    for nome in sorted(NOMES_TRANSVERSAIS):
        if nome in por_nome:
            transversais.atos.append(_ato(por_nome[nome], 0))
            usados.add(nome)
    fases.append(transversais)

    restantes = sorted(set(por_nome) - usados)
    if restantes:
        outros = Fase("Outros atos")
        outros.atos = [_ato(por_nome[nome], 0) for nome in restantes]
        fases.append(outros)
    return fases


def atos_do_papel(cod: str) -> list[Fase]:
    """Só as fases em que o cargo pratica algum ato, com apenas esses atos."""
    fases = []
    for fase in montar_linha_do_processo():
        atos = [ato for ato in fase.atos if cod in ato.papeis]
        if atos:
            fases.append(Fase(fase.nome, atos))
    return fases
