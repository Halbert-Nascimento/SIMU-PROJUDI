from __future__ import annotations

from django.db.models import Q

from processos.models import GrupoProcesso, PoloProcessual
from usuarios.models import Usuario

from .catalogo import NOME_CONTESTACAO, NOME_MP_DEVE_INTERVIR_SIM, NOME_PROTOCOLO
from .models import TipoMovimentacao


def grupo_processo_do_usuario(user, processo):
    """Vínculo do usuário com o processo específico (não qualquer grupo do ciclo)."""
    if not user.is_authenticated:
        return None
    return (
        GrupoProcesso.objects
        .filter(processo=processo, grupo__membros=user)
        .select_related("grupo", "grupo__cargo_simulacao")
        .order_by("pk")
        .first()
    )


def _mp_ocupa_polo_ativo(processo) -> bool:
    return PoloProcessual.objects.filter(
        processo=processo,
        tipo_polo=PoloProcessual.TipoPolo.ATIVO,
        grupo__cargo_simulacao__cod="MP",
    ).exists()


def _grupo_ocupa_polo_passivo(processo, grupo) -> bool:
    return PoloProcessual.objects.filter(
        processo=processo,
        tipo_polo=PoloProcessual.TipoPolo.PASSIVO,
        grupo=grupo,
    ).exists()


def pode_praticar_movimentacao(user, processo, tipo_movimentacao) -> bool:
    if tipo_movimentacao.nome_movimentacao == NOME_PROTOCOLO:
        return False  # só via cadastrar_processo — processo já existe aqui

    if not user.is_authenticated:
        return False

    if user.tipo_perfil_global in (
        Usuario.TipoPerfilGlobal.COORDENADOR,
        Usuario.TipoPerfilGlobal.PROFESSOR,
    ):
        return False

    grupo_processo = grupo_processo_do_usuario(user, processo)
    if grupo_processo is None:
        return False

    cargo = grupo_processo.grupo.cargo_simulacao
    if not tipo_movimentacao.papeis_autorizados.filter(pk=cargo.pk).exists():
        return False

    precond_ids = list(tipo_movimentacao.precondicoes.values_list("pk", flat=True))
    if precond_ids and not processo.movimentacoes.filter(tipo_movimento_id__in=precond_ids).exists():
        return False

    if tipo_movimentacao.nome_movimentacao == NOME_MP_DEVE_INTERVIR_SIM and _mp_ocupa_polo_ativo(processo):
        return False

    if tipo_movimentacao.nome_movimentacao == NOME_CONTESTACAO and not _grupo_ocupa_polo_passivo(processo, grupo_processo.grupo):
        return False

    return True


def tipos_praticaveis(user, processo):
    """Versão em lote de `pode_praticar_movimentacao`, usada na tela de registro."""
    grupo_processo = grupo_processo_do_usuario(user, processo)
    if grupo_processo is None or user.tipo_perfil_global in (
        Usuario.TipoPerfilGlobal.COORDENADOR,
        Usuario.TipoPerfilGlobal.PROFESSOR,
    ):
        return TipoMovimentacao.objects.none()

    cargo = grupo_processo.grupo.cargo_simulacao
    ja_registrados = set(processo.movimentacoes.values_list("tipo_movimento_id", flat=True))

    tipos = (
        TipoMovimentacao.objects
        .exclude(nome_movimentacao=NOME_PROTOCOLO)
        .filter(papeis_autorizados=cargo)
        .filter(Q(precondicoes__isnull=True) | Q(precondicoes__id__in=ja_registrados))
        .distinct()
    )
    if _mp_ocupa_polo_ativo(processo):
        tipos = tipos.exclude(nome_movimentacao=NOME_MP_DEVE_INTERVIR_SIM)
    if cargo.cod == "APP" and not _grupo_ocupa_polo_passivo(processo, grupo_processo.grupo):
        tipos = tipos.exclude(nome_movimentacao=NOME_CONTESTACAO)
    return tipos.order_by("nome_movimentacao")
