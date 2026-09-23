from __future__ import annotations

from .models import Notificacao
from .services import notificacoes_recentes_de


def notificacoes_usuario(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"notificacoes_nao_lidas_count": 0, "notificacoes_recentes": []}

    return {
        "notificacoes_nao_lidas_count": Notificacao.objects.filter(destinatario=user, lida=False).count(),
        "notificacoes_recentes": list(notificacoes_recentes_de(user)),
    }
