from __future__ import annotations

from django.contrib import messages


def propagar_erros_form(request, form, extra_tags: str = "") -> None:
    """
    Converte os erros de validação de um form em mensagens para o usuário.

    Substitui o laço duplo que estava repetido em acesso, ciclos, processos e
    avaliacoes.
    """
    for erros_do_campo in form.errors.values():
        for erro in erros_do_campo:
            messages.error(request, erro, extra_tags=extra_tags)
