from __future__ import annotations

from .models import MovimentacaoProcessual

NOMES_TRANSVERSAIS = {
    "Cancelamento / Tornar Sem Efeito",
    "Desentranhamento",
    "Juntada de Documentos",
}


def resolver_antecedente_logico(processo, tipo_movimentacao):
    """A movimentação mais recente do processo que satisfaz uma das pré-condições do tipo."""
    precond_ids = list(tipo_movimentacao.precondicoes.values_list("pk", flat=True))
    if not precond_ids:
        return None
    return (
        processo.movimentacoes
        .filter(tipo_movimento_id__in=precond_ids)
        .order_by("-data_movimento")
        .first()
    )


def resolver_vigente(processo, tipo_movimentacao, grupo_processo):
    """Ponta da cadeia de correções: o registro do tipo/grupo que nenhuma outra correção já substituiu."""
    if grupo_processo is None:
        return None
    candidatos = MovimentacaoProcessual.objects.filter(
        processo=processo, tipo_movimento=tipo_movimentacao, grupo_processo=grupo_processo,
    )
    return candidatos.exclude(
        movimentacoes_derivadas__tipo_movimento=tipo_movimentacao,
        movimentacoes_derivadas__grupo_processo=grupo_processo,
    ).order_by("-data_movimento").first()


def _janela_aberta(vigente) -> bool:
    if vigente is None:
        return False
    return not vigente.consequentes.filter(processo_id=vigente.processo_id).exists()


def resolver_movimentacao_origem(*, processo, tipo_movimentacao, grupo_processo, mov_origem_solicitada, confirma_correcao):
    """Decide o `movimentacao_origem` final e valida a janela de Emenda/Retificação. Retorna (origem, erro)."""
    if tipo_movimentacao.nome_movimentacao in NOMES_TRANSVERSAIS:
        return mov_origem_solicitada, None

    vigente = resolver_vigente(processo, tipo_movimentacao, grupo_processo)

    if mov_origem_solicitada is not None:
        if not _janela_aberta(vigente):
            return None, (
                f'Não é possível corrigir "{tipo_movimentacao.nome_movimentacao}": a janela de correção já '
                "foi encerrada. Use Cancelamento/Tornar Sem Efeito ou Desentranhamento a partir daqui."
            )
        return vigente, None

    if _janela_aberta(vigente):
        if not confirma_correcao:
            return None, (
                f'Já existe uma movimentação do tipo "{tipo_movimentacao.nome_movimentacao}" registrada por '
                "este grupo neste processo. Se esta é uma correção da anterior, marque a opção acima antes "
                "de salvar."
            )
        return vigente, None

    return None, None
