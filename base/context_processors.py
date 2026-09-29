from __future__ import annotations

from django.conf import settings


def session_timeout(request):
    return {"session_timeout_seconds": settings.SESSION_COOKIE_AGE}


def dados_institucionais(request):
    return {
        "nome_instituicao": settings.NOME_INSTITUICAO,
        "email_contato_dpo": settings.EMAIL_CONTATO_DPO,
        "foro_comarca": settings.FORO_COMARCA,
    }
