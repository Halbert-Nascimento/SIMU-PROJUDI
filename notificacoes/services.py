from __future__ import annotations

import logging

from django.urls import reverse

from usuarios.models import Usuario

from .models import NOTIFICACOES_RECENTES_LIMIT, Notificacao, TipoNotificacao

logger = logging.getLogger(__name__)


def notificacoes_recentes_de(usuario):
    """Últimas notificações do usuário — usado no dropdown do sino (snapshot no load e no reabrir)."""
    return (
        Notificacao.objects
        .filter(destinatario=usuario)
        .order_by("-data_criacao")[:NOTIFICACOES_RECENTES_LIMIT]
    )


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


def _bulk_criar_notificacoes(destinatarios, *, tipo, mensagem, link_url):
    """Constrói e grava uma Notificacao por destinatário — só o bulk_create, sem tratamento de erro."""
    return Notificacao.objects.bulk_create(
        Notificacao(destinatario=usuario, tipo=tipo, mensagem=mensagem, link_url=link_url)
        for usuario in destinatarios
    )


def notificar_movimentacao_registrada(movimentacao):
    """
    Notifica os membros dos grupos vinculados ao processo (GrupoProcesso),
    exceto o autor da movimentação. Roda depois do commit da movimentação
    (ver transaction.on_commit em movimentacoes.services.registrar_movimentacao),
    então uma falha aqui é só logada — nunca deve derrubar a requisição do autor.
    """
    try:
        processo = movimentacao.processo
        destinatarios = (
            Usuario.objects
            .filter(grupos_trabalho__processos=processo)
            .exclude(pk=movimentacao.autor_id)
            .distinct()
        )
        if not destinatarios:
            return []

        return _bulk_criar_notificacoes(
            destinatarios,
            tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA,
            mensagem=(
                f'Nova movimentação em "{processo.numero}": '
                f'{movimentacao.tipo_movimento.nome_movimentacao}.'
            ),
            link_url=reverse("processos:visualizar_processo", args=[processo.numero]),
        )
    except Exception:
        logger.exception("Falha ao notificar movimentacao_id=%s", movimentacao.pk)
        return []


def notificar_grupo_vinculado_processo(processo, grupo, *, ator):
    """
    Notifica os membros do grupo recém-vinculado ao processo (distribuição),
    exceto o ator. Roda depois do commit da distribuição (ver transaction.on_commit
    em processos.services.aplicar_alteracoes).
    """
    try:
        destinatarios = Usuario.objects.filter(grupos_trabalho=grupo).exclude(pk=ator.pk)
        return _bulk_criar_notificacoes(
            destinatarios,
            tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO,
            mensagem=(
                f'Seu grupo foi vinculado ao processo "{processo.numero}" '
                f'como {grupo.cargo_simulacao.nome}.'
            ),
            link_url=reverse("processos:visualizar_processo", args=[processo.numero]),
        )
    except Exception:
        logger.exception("Falha ao notificar grupo_id=%s vinculado a processo_id=%s", grupo.pk, processo.pk)
        return []


def notificar_grupo_desvinculado_processo(processo, grupo, *, ator):
    """
    Notifica os membros do grupo que saiu do processo (remoção ou substituição na
    redistribuição), exceto o ator.

    O link aponta para a área do servidor, e não para o processo: o grupo acabou de perder
    o vínculo, e em processo sob segredo de justiça `pode_visualizar_processo` recusaria a
    tela — os dois templates de notificação envolvem a linha inteira num link, então o
    aluno cairia num 403.
    """
    try:
        destinatarios = Usuario.objects.filter(grupos_trabalho=grupo).exclude(pk=ator.pk)
        return _bulk_criar_notificacoes(
            destinatarios,
            tipo=TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO,
            mensagem=(
                f'Seu grupo foi desvinculado do processo "{processo.numero}", '
                f'onde atuava como {grupo.cargo_simulacao.nome}.'
            ),
            link_url=reverse("processos:pagina_aluno"),
        )
    except Exception:
        logger.exception(
            "Falha ao notificar grupo_id=%s desvinculado de processo_id=%s", grupo.pk, processo.pk
        )
        return []


def notificar_coordenador_atribuido(*, ciclo, coordenador_anterior_id, ator):
    """Notifica o novo coordenador quando um Admin/Coordenador o designa via editar_ciclo."""
    if coordenador_anterior_id == ciclo.coordenador_id:
        return None
    if ator.pk == ciclo.coordenador_id:
        return None
    try:
        mensagem = f'Você foi designado coordenador do ciclo "{ciclo.nome_edicao}".'
        return Notificacao.objects.create(
            destinatario_id=ciclo.coordenador_id,
            tipo=TipoNotificacao.CICLO_COORDENADOR_ATRIBUIDO,
            mensagem=mensagem,
            link_url=reverse("ciclos:detalhe_ciclo", args=[ciclo.pk]),
        )
    except Exception:
        logger.exception("Falha ao notificar coordenador do ciclo_id=%s", ciclo.pk)
        return None


def notificar_participante_adicionado(*, ciclo, usuario):
    """Notifica o aluno posto num grupo do ciclo (sincroniza ciclo.participantes em adicionar_membro)."""
    try:
        mensagem = f'Você foi adicionado ao ciclo "{ciclo.nome_edicao}".'
        return Notificacao.objects.create(
            destinatario=usuario,
            tipo=TipoNotificacao.CICLO_PARTICIPANTE_ADICIONADO,
            mensagem=mensagem,
            link_url=reverse("ciclos:detalhe_ciclo", args=[ciclo.pk]),
        )
    except Exception:
        logger.exception("Falha ao notificar participante usuario_id=%s do ciclo_id=%s", usuario.pk, ciclo.pk)
        return None


def _e_transicao_notificavel(status_anterior, status_novo) -> bool:
    anterior = (status_anterior.nome_status or "").strip().lower()
    novo = (status_novo.nome_status or "").strip().lower()
    arquivando = novo == "arquivado" and anterior != "arquivado"
    reativando = anterior == "arquivado" and novo == "em andamento"
    return arquivando or reativando
