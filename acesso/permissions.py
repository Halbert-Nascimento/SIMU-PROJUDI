from __future__ import annotations

from usuarios.models import Usuario


def pode_gerenciar_usuarios(user: Usuario) -> bool:
    """
        Quem pode acessar a página de gestão de usuários.
        - Admin, Coordenador e Professor podem (Aluno e Pendente não podem).
    """
    if not user.is_authenticated:
        return False
    
    return user.tipo_perfil_global in (Usuario.TipoPerfilGlobal.ADMIN, Usuario.TipoPerfilGlobal.COORDENADOR, Usuario.TipoPerfilGlobal.PROFESSOR)

def tipos_que_pode_atribuir(ator: Usuario) -> set[str]:
    """
        Quais tipos de perfil um usuário pode atribuir a outros usuários.
        - Admin pode atribuir qualquer tipo.
        - Coordenador pode atribuir Coordenado, Professor e Aluno.
        - Professor pode atribuir aluno.
    """

    if not ator.is_authenticated:
        return set()
    
    if ator.tipo_perfil_global == Usuario.TipoPerfilGlobal.ADMIN:
        return {
            Usuario.TipoPerfilGlobal.ADMIN,
            Usuario.TipoPerfilGlobal.COORDENADOR,
            Usuario.TipoPerfilGlobal.PROFESSOR,
            Usuario.TipoPerfilGlobal.ALUNO,
        }
    
    if ator.tipo_perfil_global == Usuario.TipoPerfilGlobal.COORDENADOR:
        return {
            Usuario.TipoPerfilGlobal.COORDENADOR,
            Usuario.TipoPerfilGlobal.PROFESSOR,
            Usuario.TipoPerfilGlobal.ALUNO,
        }
    
    if ator.tipo_perfil_global == Usuario.TipoPerfilGlobal.PROFESSOR:
        return {
            Usuario.TipoPerfilGlobal.ALUNO,
        }
    
    return set()

def pode_editar_ciclo(ator: Usuario, ciclo) -> bool:
    """
        Quem pode editar um ciclo.
        - Admin pode editar qualquer ciclo.
        - Coordenador pode editar qualquer ciclo.
        - Professor pode editar os ciclos que é responsável.
    """

    if not ator.is_authenticated:
        return False
    
    if ator.tipo_perfil_global == Usuario.TipoPerfilGlobal.ADMIN:
        return True
    
    if ator.tipo_perfil_global == Usuario.TipoPerfilGlobal.COORDENADOR:
        return True
    
    if ator.tipo_perfil_global == Usuario.TipoPerfilGlobal.PROFESSOR:
        return ciclo.coordenador == ator.pk
    
    return False