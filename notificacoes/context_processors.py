from __future__ import annotations

from .models import NOTIFICACOES_RECENTES_LIMIT, Notificacao


def notificacoes_usuario(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"notificacoes_nao_lidas_count": 0, "notificacoes_recentes": []}

    notificacoes_do_usuario = Notificacao.objects.filter(destinatario=user)
    return {
        "notificacoes_nao_lidas_count": notificacoes_do_usuario.filter(lida=False).count(),
        "notificacoes_recentes": list(
            notificacoes_do_usuario.order_by("-data_criacao")[:NOTIFICACOES_RECENTES_LIMIT]
        ),
    }
