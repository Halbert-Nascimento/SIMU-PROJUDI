from __future__ import annotations

from django.db.models import Avg, Count, Q

from ciclos.models import CicloSimulacao, ParticipanteCiclo
from ciclos.permissions import pode_ver_todos_ciclos
from movimentacoes.models import MovimentacaoProcessual
from usuarios.models import Usuario

from .estrelas import faixa_da_estrela, media_em_estrelas, nota_para_estrelas
from .models import FeedbackProfessor


def feedbacks_ids_para_movimentacoes(mov_ids: list[int]) -> set[int]:
    return set(
        FeedbackProfessor.objects
        .filter(movimentacao_id__in=mov_ids)
        .values_list("movimentacao_id", flat=True)
    )


def ciclos_do_avaliador(usuario):
    """Ciclos cujas movimentações o usuário pode avaliar — o recorte de `pode_avaliar_movimentacao`."""
    ciclos = CicloSimulacao.objects.select_related("status")
    if pode_ver_todos_ciclos(usuario):
        return ciclos
    return ciclos.filter(coordenador=usuario)


def notas_por_aluno(ciclos):
    """Uma linha por aluno e ciclo: movimentações, avaliadas e média em estrelas."""
    agregados = {
        (linha["autor_id"], linha["processo__ciclo_id"]): linha
        for linha in (
            MovimentacaoProcessual.objects
            .filter(processo__ciclo__in=ciclos)
            .values("autor_id", "processo__ciclo_id")
            .annotate(
                total_movimentacoes=Count("pk", distinct=True),
                total_avaliadas=Count(
                    "pk", filter=Q(feedbacks__nota__isnull=False), distinct=True,
                ),
                media=Avg("feedbacks__nota"),
            )
            .order_by()
        )
    }

    participantes = (
        ParticipanteCiclo.objects
        .filter(
            ciclo__in=ciclos,
            usuario__tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
        )
        .select_related("usuario", "ciclo")
        .order_by("ciclo__nome_edicao", "usuario__first_name", "usuario__username")
    )

    linhas = []
    for participante in participantes:
        agregado = agregados.get((participante.usuario_id, participante.ciclo_id), {})
        estrelas = nota_para_estrelas(agregado.get("media"))
        linhas.append({
            "aluno": participante.usuario,
            "ciclo": participante.ciclo,
            "total_movimentacoes": agregado.get("total_movimentacoes", 0),
            "total_avaliadas": agregado.get("total_avaliadas", 0),
            "media": media_em_estrelas(agregado.get("media")),
            "faixa": faixa_da_estrela(estrelas),
        })
    return linhas


def media_geral_das_notas(ciclos):
    media = (
        FeedbackProfessor.objects
        .filter(
            movimentacao__processo__ciclo__in=ciclos,
            movimentacao__autor__tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
            nota__isnull=False,
        )
        .aggregate(media=Avg("nota"))["media"]
    )
    return media_em_estrelas(media)


def movimentacoes_pendentes_de_avaliacao(usuario, ciclos):
    """Movimentações dos ciclos sem nenhum feedback, fora as do próprio usuário (RN-07)."""
    return (
        MovimentacaoProcessual.objects
        .filter(processo__ciclo__in=ciclos, feedbacks__isnull=True)
        .exclude(autor=usuario)
        .select_related("tipo_movimento", "autor", "processo", "processo__ciclo")
        .order_by("data_movimento")
    )
