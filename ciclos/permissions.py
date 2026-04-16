from __future__ import annotations

from usuarios.models import Usuario


def pode_criar_ciclo(user: Usuario) -> bool:
    if not user.is_authenticated:
        return False
    return user.tipo_perfil_global in (
        Usuario.TipoPerfilGlobal.ADMIN,
        Usuario.TipoPerfilGlobal.COORDENADOR,
        Usuario.TipoPerfilGlobal.PROFESSOR,
    )


def pode_gerenciar_grupos_ciclo(user: Usuario, ciclo) -> bool:
    """
    Pode gerenciar grupos de um ciclo:
    - Admin: sempre.
    - Coordenador: somente se for o coordenador daquele ciclo.
    - Professor: somente se estiver vinculado como participante do ciclo.
    """
    if not user.is_authenticated:
        return False
    tp = user.tipo_perfil_global
    if tp == Usuario.TipoPerfilGlobal.ADMIN:
        return True
    if tp == Usuario.TipoPerfilGlobal.COORDENADOR and ciclo.coordenador_id == user.pk:
        return True
    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return ciclo.participantes.filter(pk=user.pk).exists()
    return False
