from __future__ import annotations

from django.urls import reverse

from .models import Notificacao, TipoNotificacao


def notificar_mudanca_status_ciclo(*, ciclo, status_anterior, status_novo, ator):
    """
    Notifica o coordenador do ciclo ao arquivar ou reativar (arquivado -> em
    andamento). Não notifica quando o próprio coordenador é o autor da ação.
    """
    if status_anterior.pk == status_novo.pk:
        return None
    if not _e_transicao_notificavel(status_anterior, status_novo):
        return None
    if ator.pk == ciclo.coordenador_id:
        return None

    if status_novo.nome_status.strip().lower() == "arquivado":
        mensagem = (
            f'O ciclo "{ciclo.nome_edicao}" foi arquivado por '
            f'{ator.get_full_name() or ator.username}.'
        )
    else:
        mensagem = (
            f'O ciclo "{ciclo.nome_edicao}" foi reativado (voltou para "Em andamento") '
            f'por {ator.get_full_name() or ator.username}.'
        )

    return Notificacao.objects.create(
        destinatario_id=ciclo.coordenador_id,
        tipo=TipoNotificacao.CICLO_STATUS_ALTERADO,
        mensagem=mensagem,
        link_url=reverse("ciclos:detalhe_ciclo", args=[ciclo.pk]),
    )


def _e_transicao_notificavel(status_anterior, status_novo) -> bool:
    anterior = (status_anterior.nome_status or "").strip().lower()
    novo = (status_novo.nome_status or "").strip().lower()
    arquivando = novo == "arquivado" and anterior != "arquivado"
    reativando = anterior == "arquivado" and novo == "em andamento"
    return arquivando or reativando
