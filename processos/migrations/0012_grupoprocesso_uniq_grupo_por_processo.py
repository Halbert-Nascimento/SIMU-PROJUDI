# Fecha o vínculo grupo-processo: limpa o que o modal aditivo deixou passar e só então
# impede a duplicata no banco.
#
# A limpeza NÃO é reversível — ela apaga vínculo, e `grupo_processo` das movimentações
# daquele grupo é SET_NULL. Rode com dump do banco à mão. O que foi apagado sai no log.

import logging

from django.db import migrations, models

logger = logging.getLogger(__name__)

# A serventia fica fora: ciclo com dois grupos de cartório é legítimo, e os dois precisam de
# vínculo para movimentar o mesmo processo (ver 01_implementacoes/06, decisão 2.5).
CARGOS_DE_POSICAO = ("APA", "APP", "MP", "JZ")


def _apagar(GrupoProcesso, vinculos, motivo):
    for vinculo in vinculos:
        logger.warning(
            "limpeza de vínculo duplicado (%s): processo_id=%s grupo_id=%s vinculo_id=%s",
            motivo, vinculo.processo_id, vinculo.grupo_id, vinculo.pk,
        )
    GrupoProcesso.objects.filter(pk__in=[v.pk for v in vinculos]).delete()


def limpar_duplicados(apps, schema_editor):
    GrupoProcesso = apps.get_model("processos", "GrupoProcesso")
    MovimentacaoProcessual = apps.get_model("movimentacoes", "MovimentacaoProcessual")

    vinculos = list(
        GrupoProcesso.objects
        .select_related("grupo__cargo_simulacao")
        .order_by("pk")
    )
    com_movimentacao = set(
        MovimentacaoProcessual.objects
        .filter(grupo_processo__isnull=False)
        .values_list("grupo_processo_id", flat=True)
    )

    # 1. par (processo, grupo) repetido: precisa sair para a constraint poder existir
    por_par: dict[tuple[int, int], list] = {}
    for vinculo in vinculos:
        por_par.setdefault((vinculo.processo_id, vinculo.grupo_id), []).append(vinculo)
    sobreviventes = []
    for repetidos in por_par.values():
        fica = _escolher(repetidos, com_movimentacao)
        sobreviventes.append(fica)
        _apagar(GrupoProcesso, [v for v in repetidos if v.pk != fica.pk], "par repetido")

    # 2. mesmo papel com mais de um grupo no mesmo processo
    por_papel: dict[tuple[int, str], list] = {}
    for vinculo in sobreviventes:
        cod = vinculo.grupo.cargo_simulacao.cod
        if cod in CARGOS_DE_POSICAO:
            por_papel.setdefault((vinculo.processo_id, cod), []).append(vinculo)
    for concorrentes in por_papel.values():
        if len(concorrentes) < 2:
            continue
        fica = _escolher(concorrentes, com_movimentacao)
        _apagar(GrupoProcesso, [v for v in concorrentes if v.pk != fica.pk], "papel duplicado")


def _escolher(candidatos, com_movimentacao):
    """Fica quem já atuou no processo; no empate, o vínculo mais antigo."""
    com_atos = [v for v in candidatos if v.pk in com_movimentacao]
    return (com_atos or candidatos)[0]


class Migration(migrations.Migration):

    dependencies = [
        ('ciclos', '0010_ciclosimulacao_uniq_ciclo_nome_edicao_ci_and_more'),
        ('movimentacoes', '0005_tipo_redistribuicao'),
        ('processos', '0011_polo_processual_grupo_responsavel'),
    ]

    operations = [
        migrations.RunPython(limpar_duplicados, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='grupoprocesso',
            constraint=models.UniqueConstraint(fields=('processo', 'grupo'), name='uniq_grupo_por_processo', violation_error_message='Este grupo já está vinculado ao processo.'),
        ),
    ]
