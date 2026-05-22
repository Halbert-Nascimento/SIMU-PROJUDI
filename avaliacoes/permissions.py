from __future__ import annotations

from usuarios.models import Usuario


def pode_avaliar_movimentacao(user, movimentacao) -> bool:
    if not user.is_authenticated:
        return False
    if user.tipo_perfil_global not in (
        Usuario.TipoPerfilGlobal.ADMIN,
        Usuario.TipoPerfilGlobal.COORDENADOR,
        Usuario.TipoPerfilGlobal.PROFESSOR,
    ):
        return False
    # RN-07: professor não pode avaliar movimentação que ele mesmo registrou
    if movimentacao.autor_id == user.pk:
        return False
    return True
