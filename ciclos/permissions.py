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


def pode_editar_ciclo(user: Usuario, ciclo) -> bool:
    """
    Pode editar um ciclo:
    - Admin: sempre.
    - Coordenador: sempre .
    - Professor: somente se for o coordenador daquele ciclo.
    """
    if not user.is_authenticated:
        return False
    tp = user.tipo_perfil_global
    if tp == Usuario.TipoPerfilGlobal.ADMIN:
        return True
    if tp == Usuario.TipoPerfilGlobal.COORDENADOR:
        return True
    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return ciclo.coordenador_id == user.pk
    return False


def pode_gerenciar_grupos_ciclo(user: Usuario, ciclo) -> bool:
    """
    Pode gerenciar grupos de um ciclo:
    - Admin: sempre.
    - Coordenador: sempre.
    - Professor: somente se estiver vinculado como coodenador do ciclo.
    """
    if not user.is_authenticated:
        return False
    tp = user.tipo_perfil_global
    if tp == Usuario.TipoPerfilGlobal.ADMIN:
        return True
    if tp == Usuario.TipoPerfilGlobal.COORDENADOR:
        return True
    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return ciclo.participantes.filter(pk=user.pk).exists() or ciclo.coordenador == user
    return False


def pode_trocar_ciclo_ativo(user: Usuario) -> bool:
    """
    Quem troca de ciclo pela barra do cabeçalho.

    Só o Aluno: ele atua dentro de um ciclo por vez. Admin, Coordenador e
    Professor enxergam todos os ciclos pelo painel, e o seletor sugeriria um
    escopo que as telas deles não têm.
    """
    if not user.is_authenticated:
        return False
    return user.tipo_perfil_global == Usuario.TipoPerfilGlobal.ALUNO


def pode_ver_todos_ciclos(user: Usuario) -> bool:
    if not user.is_authenticated:
        return False
    return user.tipo_perfil_global in (
        Usuario.TipoPerfilGlobal.ADMIN,
        Usuario.TipoPerfilGlobal.COORDENADOR,
    )


def pode_ver_ciclos_arquivados(user: Usuario) -> bool:
    if not user.is_authenticated:
        return False
    return user.tipo_perfil_global in (
        Usuario.TipoPerfilGlobal.ADMIN,
        Usuario.TipoPerfilGlobal.COORDENADOR,
    )
