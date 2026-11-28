from __future__ import annotations

from ciclos.permissions import pode_alterar_autos_no_ciclo
from usuarios.models import Usuario


def pode_criar_parte(user, ciclo) -> bool:
    """
    Parte fictícia nasce no cadastro de processo e vale a mesma regra: qualquer
    papel, desde que o ciclo ativo esteja "Em andamento".
    """
    if not user.is_authenticated or ciclo is None:
        return False
    return pode_alterar_autos_no_ciclo(ciclo)


def pode_editar_processo(user, processo) -> bool:
    """
    Alterar dados do processo e das partes: exige ciclo "Em andamento" e o papel
    de `pode_manter_autos`.
    """
    return pode_alterar_autos_no_ciclo(processo.ciclo) and pode_manter_autos(
        user, processo
    )


def pode_manter_autos(user, processo) -> bool:
    """
    Quem tem o papel de manter os autos, sem olhar o estado do ciclo.

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


def grupo_serventia_do_usuario(user, ciclo):
    """Vínculo do usuário com a serventia (grupo de cargo SC) do ciclo, ou None."""
    if not user.is_authenticated:
        return None
    return user.grupos_trabalho.filter(ciclo=ciclo, cargo_simulacao__cod="SC").first()


def pode_ver_documentos_das_partes(user) -> bool:
    """CPF/CNPJ completo é só para quem tem login; o visitante vê mascarado."""
    return user.is_authenticated


def pode_baixar_anexos(user, processo) -> bool:
    """Anexo pode trazer dados reais de alunos: exige login além de ver o processo."""
    return user.is_authenticated and pode_visualizar_processo(user, processo)


def pode_visualizar_processo(user, processo) -> bool:
    """
    Processo sem segredo de justiça e já autuado: público, qualquer pessoa acessa sem login.
    O visitante anônimo recebe a consulta restrita: ver `pode_ver_documentos_das_partes`
    e `pode_baixar_anexos`.
    Processo com segredo de justiça, ou ainda não autuado (status "Protocolado" — só o
    grupo do protocolo está vinculado, a Autuação é quem expõe o processo pra quem mais atua):
      - Admin / Coordenador global: acesso irrestrito.
      - Professor: somente se for o coordenador do ciclo do processo.
      - Aluno em grupo Serventia (cod="SC") do ciclo: vê todos os processos do ciclo.
      - Aluno em outro grupo: somente se o grupo estiver vinculado ao processo.
      - Demais / não autenticado: negado.
    """
    if not processo.segredo_justica and processo.status_atual.nome_status != "Protocolado":
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
