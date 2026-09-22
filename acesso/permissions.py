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


def pode_editar_usuario(ator: Usuario, alvo: Usuario) -> bool:
    """
        Quem pode editar os dados de quem — status ativo, tipo de perfil e senha, tudo sob a
        mesma hierarquia: são a mesma decisão de autoridade, não regras separadas.
        - Autoalteração (ator == alvo): sempre permitida — é a tela "Minha conta".
        - Admin: qualquer usuário.
        - Coordenador: Professor, Aluno e Pendente (nunca outro Coordenador ou Admin).
        - Professor: Aluno e Pendente (nunca outro Professor, Coordenador ou Admin).
        - Aluno / Pendente: nenhum outro usuário.

        Usada como gate do formulário inteiro em AtualizarUsuarioForm.clean() (corrige a
        validação do tipo ATUAL do alvo, que antes só conferia o tipo de destino) e, dentro
        dela, por redefinir_senha() para autorizar especificamente a troca de senha.
    """
    if not ator.is_authenticated:
        return False

    if ator.pk == alvo.pk:
        return True

    tp_ator = ator.tipo_perfil_global
    tp_alvo = alvo.tipo_perfil_global

    if tp_ator == Usuario.TipoPerfilGlobal.ADMIN:
        return True

    if tp_ator == Usuario.TipoPerfilGlobal.COORDENADOR:
        return tp_alvo in (
            Usuario.TipoPerfilGlobal.PROFESSOR,
            Usuario.TipoPerfilGlobal.ALUNO,
            Usuario.TipoPerfilGlobal.PENDENTE,
        )

    if tp_ator == Usuario.TipoPerfilGlobal.PROFESSOR:
        return tp_alvo in (
            Usuario.TipoPerfilGlobal.ALUNO,
            Usuario.TipoPerfilGlobal.PENDENTE,
        )

    return False
