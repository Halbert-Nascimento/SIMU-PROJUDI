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
