from __future__ import annotations

from django.db import transaction

from movimentacoes.catalogo import NOME_REDISTRIBUICAO
from movimentacoes.models import TipoMovimentacao
from movimentacoes.services import registrar_movimentacao
from notificacoes.services import (
    notificar_grupo_desvinculado_processo,
    notificar_grupo_vinculado_processo,
)

from .models import GrupoProcesso, PoloProcessual

NOME_AUTUACAO = "Autuação e Distribuição"

_POLO_DO_CARGO = {
    "APA": PoloProcessual.TipoPolo.ATIVO,
    "APP": PoloProcessual.TipoPolo.PASSIVO,
}


def _descrever_alteracoes(entraram, sairam) -> str:
    partes = []
    if entraram:
        partes.append("Grupo(s) vinculado(s): " + ", ".join(g.nome for g in entraram) + ".")
    if sairam:
        partes.append("Grupo(s) desvinculado(s): " + ", ".join(g.nome for g in sairam) + ".")
    return " ".join(partes)


def aplicar_grupos(processo, *, grupos_adicionar, grupos_remover, ator, grupo_serventia):
    """
    Aplica num processo as trocas de grupo pedidas pelo serventuário.

    `grupos_adicionar` são vinculados, substituindo quem já ocupa o mesmo papel (cargo) —
    nunca fica mais de um grupo por papel, exceto SC, que aceita vários (ciclo pode ter mais
    de um grupo de cartório). `grupos_remover` são desvinculados. Os dois argumentos precisam
    vir com `cargo_simulacao` pré-carregado (select_related), porque a resolução do papel
    roda por grupo já vinculado, sem query nova.

    Ajusta o polo de quem entra e de quem sai, registra um único evento nos autos —
    "Autuação e Distribuição" na primeira distribuição de um processo Protocolado,
    "Redistribuição" depois disso, inclusive quando o pedido é só remoção — e notifica quem
    entrou e quem saiu. Não faz nada se o pedido não muda o estado atual (idempotente).
    """
    with transaction.atomic():
        vinculos = {
            v.grupo_id: v
            for v in GrupoProcesso.objects.filter(processo=processo)
            .select_related("grupo__cargo_simulacao")
        }

        entraram = []
        sairam = []

        for grupo in grupos_remover:
            vinculo = vinculos.pop(grupo.pk, None)
            if vinculo is not None:
                vinculo.delete()
                sairam.append(grupo)

        for grupo in grupos_adicionar:
            if grupo.pk in vinculos:
                continue  # já vinculado — o polo pode não estar, é regularizado abaixo
            cod = grupo.cargo_simulacao.cod
            # SC fica fora da regra de "um grupo por papel": ciclo com dois grupos de
            # cartório é legítimo, e os dois precisam do vínculo pra movimentar o processo.
            if cod != "SC":
                ocupante = next(
                    (v for v in vinculos.values() if v.grupo.cargo_simulacao.cod == cod),
                    None,
                )
                if ocupante is not None:
                    del vinculos[ocupante.grupo_id]
                    ocupante.delete()
                    sairam.append(ocupante.grupo)
            vinculos[grupo.pk] = GrupoProcesso.objects.create(processo=processo, grupo=grupo)
            entraram.append(grupo)

        # Nem todo grupo de grupos_adicionar é vínculo novo: quem peticionou antes da
        # autuação já está vinculado sem polo, e é esta chamada que regulariza isso — por
        # isso o polo é reescrito pra todo grupo pedido, não só pra quem entrou agora.
        polos_do_pedido = {
            grupo.pk: (_POLO_DO_CARGO[grupo.cargo_simulacao.cod], grupo)
            for grupo in grupos_adicionar
            if grupo.cargo_simulacao.cod in _POLO_DO_CARGO
        }
        polos_atuais = dict(
            PoloProcessual.objects.filter(
                processo=processo, tipo_polo__in=_POLO_DO_CARGO.values()
            ).values_list("tipo_polo", "grupo_id")
        )
        polo_mudou = any(
            polos_atuais.get(polo) != grupo.pk for polo, grupo in polos_do_pedido.values()
        )

        if not entraram and not sairam and not polo_mudou:
            return

        for grupo in sairam:
            polo = _POLO_DO_CARGO.get(grupo.cargo_simulacao.cod)
            if polo:
                PoloProcessual.objects.filter(
                    processo=processo, tipo_polo=polo, grupo=grupo
                ).update(grupo=None)
        for polo, grupo in polos_do_pedido.values():
            PoloProcessual.objects.filter(processo=processo, tipo_polo=polo).update(grupo=grupo)

        protocolado = processo.status_atual.nome_status == "Protocolado"
        # autuando: primeira distribuição de fato (entra grupo, ou só regulariza o polo do
        # protocolante). Remoção pura num Protocolado não autua, mas ainda vira Redistribuição.
        autuando = protocolado and (bool(entraram) or polo_mudou)
        nome_tipo = NOME_AUTUACAO if autuando else NOME_REDISTRIBUICAO
        tipo_movimentacao = TipoMovimentacao.objects.select_related("efeito_status").get(
            nome_movimentacao=nome_tipo
        )
        grupo_processo_serventia, _ = GrupoProcesso.objects.get_or_create(
            processo=processo, grupo=grupo_serventia
        )
        registrar_movimentacao(
            processo=processo,
            autor=ator,
            tipo_movimentacao=tipo_movimentacao,
            descricao_evento=_descrever_alteracoes(entraram, sairam),
            grupo_processo=grupo_processo_serventia,
        )

        for grupo in entraram:
            transaction.on_commit(
                lambda p=processo, g=grupo: notificar_grupo_vinculado_processo(p, g, ator=ator)
            )
        for grupo in sairam:
            transaction.on_commit(
                lambda p=processo, g=grupo: notificar_grupo_desvinculado_processo(p, g, ator=ator)
            )
