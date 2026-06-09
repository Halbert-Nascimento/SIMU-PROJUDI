def ciclo_ativo(request):
    """
    Injeta ciclo_ativo e ciclos_disponiveis no contexto de todos os templates.
    Os dados são lidos do request (populados pelo CicloAtivoMiddleware), sem query extra.
    """
    return {
        "ciclo_ativo": getattr(request, "ciclo_ativo", None),
        "ciclos_disponiveis": getattr(request, "ciclos_ativos_usuario", []),
    }
