from __future__ import annotations

from functools import wraps

from django.http import Http404


def exige_permissao(*funcoes_permissao):
    """
    Aplica funções puras de permissions.py como guarda de view.

    Responde 404 em vez de 403 — comportamento que as views já adotavam, para
    não revelar a existência do recurso a quem não pode vê-lo.

        @login_required
        @exige_permissao(pode_gerenciar_usuarios, tipos_que_pode_atribuir)
        def usuario_lista(request): ...
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            for funcao in funcoes_permissao:
                if not funcao(request.user):
                    raise Http404()
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
