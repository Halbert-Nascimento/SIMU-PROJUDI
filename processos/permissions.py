from __future__ import annotations

from usuarios.models import Usuario


def pode_editar_processo(user, processo) -> bool:
    """
    Quem pode manter os autos: alterar dados do processo e dados das partes.

    Ver um processo sem segredo de justiça é público, mas alterar não pode ser:
    a regra aqui é a de quem *atua* no processo.
      - Admin / Coordenador global: sempre.
      - Professor: somente no ciclo que coordena.
      - Aluno em grupo Serventia (cod="SC") do ciclo: é o papel que mantém o
        cadastro dos autos.
      - Demais / não autenticado: negado.
    """
    if not user.is_authenticated:
        return False

    tp = user.tipo_perfil_global

    if tp in (Usuario.TipoPerfilGlobal.ADMIN, Usuario.TipoPerfilGlobal.COORDENADOR):
        return True

    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return processo.ciclo.coordenador_id == user.pk

    return user.grupos_trabalho.filter(
        ciclo=processo.ciclo,
        cargo_simulacao__cod="SC",
    ).exists()


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


def pode_movimentar_processo(user, processo) -> bool:
    """
    Quem pode praticar atos no processo: registrar e editar movimentações.

    Deliberadamente NÃO é `pode_visualizar_processo`: aquela função libera todo
    processo sem segredo de justiça para qualquer visitante, e usá-la como guarda
    de escrita transformaria "o processo é público" em "qualquer um atua nele".

    Também não é `pode_editar_processo`, que é mais estrita: manter o cadastro
    dos autos cabe só à Serventia, mas movimentar cabe a todo grupo que atua no
    processo.
      - Admin / Coordenador global: sempre.
      - Professor: somente no ciclo que coordena.
      - Aluno em grupo Serventia (cod="SC") do ciclo: em qualquer processo do ciclo.
      - Aluno em grupo diretamente vinculado ao processo: neste processo.
      - Demais / não autenticado: negado.
    """
    if not user.is_authenticated:
        return False

    tp = user.tipo_perfil_global

    if tp in (Usuario.TipoPerfilGlobal.ADMIN, Usuario.TipoPerfilGlobal.COORDENADOR):
        return True

    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        return processo.ciclo.coordenador_id == user.pk

    if user.grupos_trabalho.filter(
        ciclo=processo.ciclo,
        cargo_simulacao__cod="SC",
    ).exists():
        return True

    return processo.grupos.filter(membros=user).exists()


def pode_editar_movimentacao(user, movimentacao) -> bool:
    """
    Editar uma movimentação cria uma nova versão dela nos autos, com autoria.
    Além de poder atuar no processo, quem edita precisa ser o autor da peça —
    ou alguém que mantém os autos (Serventia, Professor do ciclo, Admin).
    """
    processo = movimentacao.processo

    if not pode_movimentar_processo(user, processo):
        return False

    return movimentacao.autor_id == user.pk or pode_editar_processo(user, processo)
