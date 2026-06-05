from __future__ import annotations

from .models import FeedbackProfessor


def feedbacks_ids_para_movimentacoes(mov_ids: list[int]) -> set[int]:
    return set(
        FeedbackProfessor.objects
        .filter(movimentacao_id__in=mov_ids)
        .values_list("movimentacao_id", flat=True)
    )
