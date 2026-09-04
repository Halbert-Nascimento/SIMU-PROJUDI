from .permissions import pode_trocar_ciclo_ativo


def ciclo_ativo(request):
    """
    Injeta ciclo_ativo e ciclos_disponiveis no contexto de todos os templates.
    Os dados são lidos do request (populados pelo CicloAtivoMiddleware), sem query extra.

    `pode_trocar_ciclo` vem da permissão em vez de uma lista de perfis no
    template: repetir a lista deixaria a barra e a regra livres para divergir.
    """
    user = getattr(request, "user", None)
    return {
        "ciclo_ativo": getattr(request, "ciclo_ativo", None),
        "ciclos_disponiveis": getattr(request, "ciclos_ativos_usuario", []),
        "pode_trocar_ciclo": bool(user and pode_trocar_ciclo_ativo(user)),
    }
