from __future__ import annotations

from usuarios.models import Usuario


def pode_ver_minhas_notas(user) -> bool:
    return user.is_authenticated and user.tipo_perfil_global == Usuario.TipoPerfilGlobal.ALUNO


def perfil_pode_avaliar(user) -> bool:
    return user.is_authenticated and user.tipo_perfil_global in (
        Usuario.TipoPerfilGlobal.ADMIN,
        Usuario.TipoPerfilGlobal.COORDENADOR,
        Usuario.TipoPerfilGlobal.PROFESSOR,
    )


def pode_avaliar_movimentacao(user, movimentacao) -> bool:
    if not perfil_pode_avaliar(user):
        return False
    # RN-07: ninguém avalia movimentação que ele mesmo registrou
    if movimentacao.autor_id == user.pk:
        return False
    tp = user.tipo_perfil_global
    if tp in (Usuario.TipoPerfilGlobal.ADMIN, Usuario.TipoPerfilGlobal.COORDENADOR):
        return True
    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return movimentacao.processo.ciclo.coordenador_id == user.pk
    return False
