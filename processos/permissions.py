from __future__ import annotations

from usuarios.models import Usuario


def pode_visualizar_processo(user, processo) -> bool:
    """
    Processo sem segredo de justiça: público, qualquer pessoa acessa sem login.
    Processo com segredo de justiça:
      - Admin / Coordenador global: acesso irrestrito.
      - Professor: somente se for o coordenador do ciclo do processo.
      - Aluno em grupo Serventia (cod="SC") do ciclo: vê todos os processos do ciclo.
      - Aluno em outro grupo: somente se o grupo estiver vinculado ao processo.
      - Demais / não autenticado: negado.
    """
    if not processo.segredo_justica:
        return True

    if not user.is_authenticated:
        return False

    tp = user.tipo_perfil_global

    if tp in (Usuario.TipoPerfilGlobal.ADMIN, Usuario.TipoPerfilGlobal.COORDENADOR):
        return True

    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return processo.ciclo.coordenador_id == user.pk

    # Aluno em grupo Serventia do ciclo deste processo
    if user.grupos_trabalho.filter(
        ciclo=processo.ciclo,
        cargo_simulacao__cod="SC",
    ).exists():
        return True

    # Aluno em grupo diretamente vinculado ao processo
    if processo.grupos.filter(membros=user).exists():
        return True

    return False
