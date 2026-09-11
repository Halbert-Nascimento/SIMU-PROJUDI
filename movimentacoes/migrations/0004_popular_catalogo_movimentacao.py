# Popula o catálogo fechado de TipoMovimentacao (83 sequenciais + 3 transversais) e liga papéis, pré-condições, efeito sobre status e efeitos colaterais.

from django.db import migrations

STATUS_FALTANTES = [
    "Extinto sem resolução do mérito",
    "Em Citação",
    "Citado",
    "Em Fase de Defesa",
    "Em Instrução",
    "Publicado/Aguardando Prazo Recursal",
    "Em Fase Recursal",
    "Remetido ao 2º Grau",
    "Transitado em Julgado",
]

TIPOS_LEGADOS_REAPROVEITADOS = {
    1: "Protocolo da Petição Inicial",
    3: "Conclusão ao Juiz",
    4: "SENTENÇA",
    5: "Custas Recolhidas",
    6: "Custas Não Recolhidas",
    7: "Intima autor p/ custas",
    8: "Custas Pagas Após Intimação",
    9: "Custas Não Pagas Após Intimação",
    10: "Cancelamento da Distribuição",
    11: "TRÂNSITO EM JULGADO",
    12: "Arquivamento",
}

# cada linha: (nome, papéis autorizados, pré-condições "ou", efeito sobre status, efeitos colaterais)
CATALOGO = [
    ("Protocolo da Petição Inicial", ("APA", "MP"), (), "Protocolado", ()),
    ("Autuação e Distribuição", ("SC",), ("Protocolo da Petição Inicial",), "Autuado", ()),
    ("Custas Recolhidas", ("SC",), ("Autuação e Distribuição",), None, ()),
    ("Custas Não Recolhidas", ("SC",), ("Autuação e Distribuição",), None, ()),
    ("Intima autor p/ custas", ("SC",), ("Custas Não Recolhidas",), None, ("abre_prazo",)),
    ("Custas Pagas Após Intimação", ("SC",), ("Intima autor p/ custas",), None, ("encerra_prazo",)),
    ("Custas Não Pagas Após Intimação", ("SC",), ("Intima autor p/ custas",), None, ("encerra_prazo",)),
    ("Cancelamento da Distribuição", ("JZ",), ("Custas Não Pagas Após Intimação",), "Extinto sem resolução do mérito", ()),
    ("Conclusão ao Juiz", ("SC",), ("Custas Recolhidas", "Custas Pagas Após Intimação", "Emenda Apresentada"), None, ()),
    ("Análise da Inicial — Irregular", ("JZ",), ("Conclusão ao Juiz",), None, ()),
    ("Análise da Inicial — Urgente", ("JZ",), ("Conclusão ao Juiz",), None, ()),
    ("Análise da Inicial — Indefere", ("JZ",), ("Conclusão ao Juiz",), None, ()),
    ("Análise da Inicial — Em Ordem", ("JZ",), ("Conclusão ao Juiz",), None, ()),
    ("Emenda da Inicial", ("JZ",), ("Análise da Inicial — Irregular",), None, ("abre_prazo",)),
    ("Emenda Apresentada", ("APA", "MP"), ("Emenda da Inicial",), None, ("encerra_prazo",)),
    ("Emenda Não Apresentada", ("SC",), ("Emenda da Inicial",), None, ("encerra_prazo",)),
    ("Indeferimento da Inicial", ("JZ",), ("Análise da Inicial — Indefere", "Emenda Não Apresentada"), "Extinto sem resolução do mérito", ()),
    ("Tutela de Urgência Deferida", ("JZ",), ("Análise da Inicial — Urgente",), None, ()),
    ("Tutela de Urgência Indeferida", ("JZ",), ("Análise da Inicial — Urgente",), None, ()),
    ("Liminar Concedida", ("JZ",), ("Tutela de Urgência Deferida",), None, ()),
    ("Despacho de Citação", ("JZ",), ("Análise da Inicial — Em Ordem", "Tutela de Urgência Indeferida", "Liminar Concedida"), "Em Citação", ()),
    ("Modalidade de Citação — Mandado", ("SC",), ("Despacho de Citação",), None, ()),
    ("Modalidade de Citação — Postal", ("SC",), ("Despacho de Citação",), None, ()),
    ("Modalidade de Citação — Edital", ("SC",), ("Despacho de Citação",), None, ()),
    ("Modalidade de Citação — Eletrônica", ("SC",), ("Despacho de Citação",), None, ()),
    ("Citação por Mandado", ("SC",), ("Modalidade de Citação — Mandado", "Nova Modalidade — Repetir Mandado"), None, ()),
    ("Citação por Carta Postal (AR)", ("SC",), ("Modalidade de Citação — Postal",), None, ()),
    ("Citação por Edital", ("SC",), ("Modalidade de Citação — Edital", "Nova Modalidade — Edital"), "Citado", ("abre_prazo",)),
    ("Citação Eletrônica/Portal", ("SC",), ("Modalidade de Citação — Eletrônica",), "Citado", ("agenda_audiencia",)),
    ("Cumprimento do Mandado — Réu Encontrado", ("SC",), ("Citação por Mandado",), None, ()),
    ("Cumprimento do Mandado — Réu Não Encontrado", ("SC",), ("Citação por Mandado",), None, ()),
    ("Citação Positiva", ("SC",), ("Cumprimento do Mandado — Réu Encontrado",), "Citado", ("agenda_audiencia",)),
    ("Citação Negativa", ("SC",), ("Cumprimento do Mandado — Réu Não Encontrado",), None, ()),
    ("Nova Modalidade — Edital", ("JZ",), ("Citação Negativa", "AR Não Assinado ou Não Devolvido"), None, ()),
    ("Nova Modalidade — Repetir Mandado", ("SC",), ("Citação Negativa", "AR Não Assinado ou Não Devolvido"), None, ()),
    ("AR Assinado Juntado", ("SC",), ("Citação por Carta Postal (AR)",), "Citado", ("agenda_audiencia",)),
    ("AR Não Assinado ou Não Devolvido", ("SC",), ("Citação por Carta Postal (AR)",), None, ()),
    ("Audiência de Conciliação — Com Acordo", ("JZ",), ("Citação Eletrônica/Portal", "Citação Positiva", "AR Assinado Juntado", "Citação por Edital"), None, ()),
    ("Audiência de Conciliação — Sem Acordo", ("JZ",), ("Citação Eletrônica/Portal", "Citação Positiva", "AR Assinado Juntado", "Citação por Edital"), "Em Fase de Defesa", ("abre_prazo",)),
    ("Contestação", ("APP",), ("Audiência de Conciliação — Sem Acordo",), None, ("encerra_prazo",)),
    ("Revelia", ("SC",), ("Audiência de Conciliação — Sem Acordo",), None, ("encerra_prazo",)),
    ("Efeitos da Revelia — Produz Efeitos", ("JZ",), ("Revelia",), None, ()),
    ("Efeitos da Revelia — Sem Efeito", ("JZ",), ("Revelia",), None, ()),
    ("Julgamento Antecipado", ("JZ",), ("Efeitos da Revelia — Produz Efeitos", "Provas a Produzir — Só Documental"), None, ()),
    ("Réplica do Autor", ("APA", "APP", "MP"), ("Contestação", "Efeitos da Revelia — Sem Efeito"), None, ()),
    ("MP Deve Intervir — Sim", ("JZ",), ("Réplica do Autor",), None, ("notifica",)),
    ("MP Deve Intervir — Não", ("JZ",), ("Réplica do Autor",), None, ()),
    ("Manifestação do MP", ("MP",), ("MP Deve Intervir — Sim",), None, ()),
    ("Decisão Saneadora", ("JZ",), ("MP Deve Intervir — Não", "Manifestação do MP"), "Em Instrução", ()),
    ("Provas a Produzir — Perícia", ("JZ",), ("Decisão Saneadora",), None, ()),
    ("Provas a Produzir — Prova Oral", ("JZ",), ("Decisão Saneadora",), None, ("agenda_audiencia",)),
    ("Provas a Produzir — Só Documental", ("JZ",), ("Decisão Saneadora",), None, ()),
    ("Prova Pericial", ("JZ",), ("Provas a Produzir — Perícia",), None, ()),
    ("Laudo Pericial juntado", ("SC",), ("Prova Pericial",), None, ("agenda_audiencia",)),
    ("Audiência de Instrução e Julgamento", ("JZ",), ("Provas a Produzir — Prova Oral", "Laudo Pericial juntado"), None, ()),
    ("Resultado da Audiência — Acordo", ("JZ",), ("Audiência de Instrução e Julgamento",), None, ()),
    ("Resultado da Audiência — Memoriais", ("JZ",), ("Audiência de Instrução e Julgamento",), None, ()),
    ("Resultado da Audiência — Julgamento na Data", ("JZ",), ("Audiência de Instrução e Julgamento",), None, ()),
    ("Acordo em Audiência", ("JZ",), ("Resultado da Audiência — Acordo",), None, ()),
    ("Memoriais/Alegações Finais", ("APA", "APP", "MP"), ("Resultado da Audiência — Memoriais",), None, ()),
    ("Sentença Homologatória de Acordo", ("JZ",), ("Acordo em Audiência", "Audiência de Conciliação — Com Acordo"), "Sentenciado", ()),
    ("SENTENÇA", ("JZ",), ("Julgamento Antecipado", "Resultado da Audiência — Julgamento na Data", "Memoriais/Alegações Finais"), "Sentenciado", ()),
    ("Tipo de Sentença — Com Mérito", ("JZ",), ("SENTENÇA",), None, ()),
    ("Tipo de Sentença — Sem Mérito", ("JZ",), ("SENTENÇA",), None, ()),
    ("Com resolução do mérito", ("JZ",), ("Tipo de Sentença — Com Mérito",), None, ()),
    ("Sem resolução do mérito", ("JZ",), ("Tipo de Sentença — Sem Mérito",), None, ()),
    ("Publicação/Intimação das Partes", ("SC",), ("Com resolução do mérito", "Sem resolução do mérito"), "Publicado/Aguardando Prazo Recursal", ("notifica", "abre_prazo")),
    ("Embargos de Declaração", ("APA", "APP", "MP"), ("Publicação/Intimação das Partes", "Decisão nos Embargos"), "Em Fase Recursal", ("encerra_prazo",)),
    ("Decisão nos Embargos", ("JZ",), ("Embargos de Declaração",), None, ("reabre_prazo",)),
    ("Apelação", ("APA", "APP", "MP"), ("Indeferimento da Inicial", "Publicação/Intimação das Partes", "Decisão nos Embargos"), "Em Fase Recursal", ("encerra_prazo",)),
    ("Contrarrazões", ("APA", "APP", "MP"), ("Apelação",), None, ()),
    ("Remessa ao 2º Grau", ("SC",), ("Contrarrazões",), "Remetido ao 2º Grau", ()),
    ("Julgamento pelo Tribunal", (), ("Remessa ao 2º Grau",), None, ()),
    ("Recurso Provido", (), ("Julgamento pelo Tribunal",), None, ()),
    ("Recurso Não Provido", (), ("Julgamento pelo Tribunal",), None, ()),
    ("Provimento Parcial", (), ("Julgamento pelo Tribunal",), None, ()),
    ("Recurso Não Conhecido", (), ("Julgamento pelo Tribunal",), None, ()),
    ("Baixa dos Autos ao 1º Grau", (), ("Recurso Provido", "Recurso Não Provido", "Provimento Parcial", "Recurso Não Conhecido"), None, ()),
    ("Recurso Superior? (STJ/STF)", ("APA", "APP", "MP"), ("Baixa dos Autos ao 1º Grau",), None, ()),
    ("REsp/RE (STJ/STF)", ("APA", "APP", "MP"), ("Recurso Superior? (STJ/STF)",), None, ()),
    ("TRÂNSITO EM JULGADO", ("SC",), ("Sentença Homologatória de Acordo", "Publicação/Intimação das Partes", "Decisão nos Embargos", "Recurso Superior? (STJ/STF)", "REsp/RE (STJ/STF)"), "Transitado em Julgado", ()),
    ("Certidão de Trânsito em Julgado", ("SC",), ("TRÂNSITO EM JULGADO",), None, ()),
    ("Arquivamento", ("SC",), ("Certidão de Trânsito em Julgado",), "Arquivado", ()),
]

TRANSVERSAIS = [
    ("Cancelamento / Tornar Sem Efeito", ("SC",), (), None, ()),
    ("Desentranhamento", ("JZ",), (), None, ()),
    ("Juntada de Documentos", ("APA", "APP", "MP"), (), None, ()),
]


def popular(apps, schema_editor):
    StatusProcessoJudicial = apps.get_model("processos", "StatusProcessoJudicial")
    CargoSimulacao = apps.get_model("ciclos", "CargoSimulacao")
    TipoMovimentacao = apps.get_model("movimentacoes", "TipoMovimentacao")
    PapelAutorizadoMovimentacao = apps.get_model("movimentacoes", "PapelAutorizadoMovimentacao")
    PreCondicaoMovimentacao = apps.get_model("movimentacoes", "PreCondicaoMovimentacao")
    EfeitoColateralMovimentacao = apps.get_model("movimentacoes", "EfeitoColateralMovimentacao")

    for nome in STATUS_FALTANTES:
        StatusProcessoJudicial.objects.get_or_create(nome_status=nome)

    for old_id, novo_nome in TIPOS_LEGADOS_REAPROVEITADOS.items():
        TipoMovimentacao.objects.filter(pk=old_id).update(nome_movimentacao=novo_nome)

    todas_linhas = CATALOGO + TRANSVERSAIS
    for nome, _papeis, _precond, _status, _efeitos in todas_linhas:
        TipoMovimentacao.objects.get_or_create(nome_movimentacao=nome)

    tipos_por_nome = {t.nome_movimentacao: t for t in TipoMovimentacao.objects.all()}
    cargos_por_cod = {c.cod: c for c in CargoSimulacao.objects.all()}
    status_por_nome = {s.nome_status: s for s in StatusProcessoJudicial.objects.all()}

    for nome, papeis, _precond, status_nome, efeitos in todas_linhas:
        tipo = tipos_por_nome[nome]
        for cod in papeis:
            PapelAutorizadoMovimentacao.objects.get_or_create(
                tipo_movimentacao=tipo, cargo_simulacao=cargos_por_cod[cod],
            )
        if status_nome:
            tipo.efeito_status = status_por_nome[status_nome]
            tipo.save(update_fields=["efeito_status"])
        for categoria in efeitos:
            EfeitoColateralMovimentacao.objects.get_or_create(
                tipo_movimentacao=tipo, categoria=categoria,
            )

    for nome, _papeis, precond, _status, _efeitos in todas_linhas:
        tipo = tipos_por_nome[nome]
        for nome_precondicao in precond:
            PreCondicaoMovimentacao.objects.get_or_create(
                tipo_movimentacao=tipo, precondicao=tipos_por_nome[nome_precondicao],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("movimentacoes", "0003_papeis_precondicoes_efeitos_colaterais"),
    ]

    operations = [
        migrations.RunPython(popular, migrations.RunPython.noop),
    ]
