from __future__ import annotations

import json

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ciclos.models import GrupoTrabalho
from movimentacoes.catalogo import NOME_AUTUACAO, NOME_REDISTRIBUICAO
from movimentacoes.models import MovimentacaoProcessual, TipoMovimentacao
from notificacoes.models import Notificacao, TipoNotificacao
from processos.models import GrupoProcesso, PoloProcessual
from processos.permissions import pode_editar_processo, pode_visualizar_processo
from processos.services import aplicar_grupos

from .fixtures import CenarioMovimentacoesTestCase


class ExtrasProcessosTests(CenarioMovimentacoesTestCase):
    """Testes adicionais de valor real, além do Ponto 9 literal do mapa."""

    def test_remover_grupos_zera_polo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        self.autuar_processo(processo, [])
        self.assertEqual(processo.grupos.count(), 0)
        for polo in PoloProcessual.objects.filter(processo=processo):
            self.assertIsNone(polo.grupo_id)

    def test_remover_tudo_registra_redistribuicao_e_notifica(self):
        """'Desvincular Grupos' em massa precisa passar por aplicar_grupos() como
        qualquer outra troca — sem isso o histórico se perde (grupo_processo das
        movimentações antigas é SET_NULL) e ninguém é avisado da remoção."""
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])  # também vincula o SC do ator

        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, [])

        movimentacao = (
            MovimentacaoProcessual.objects.filter(processo=processo)
            .order_by("-data_movimento", "-pk")
            .first()
        )
        self.assertEqual(movimentacao.tipo_movimento.nome_movimentacao, "Redistribuição")
        self.assertIsNone(movimentacao.grupo_processo_id)
        self.assertIn("desvinculado", movimentacao.descricao_evento.lower())

        # o SC é o ator da remoção: notificar_grupo_desvinculado_processo exclui o
        # próprio ator, então só APA e APP (que não agiram) recebem o aviso
        destinatarios = set(
            Notificacao.objects.filter(tipo=TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO)
            .values_list("destinatario_id", flat=True)
        )
        self.assertEqual(destinatarios, {self.usuarios["APA"].pk, self.usuarios["APP"].pk})

    def test_sc_aceita_multiplos_grupos_sem_substituir(self):
        """SC fica fora da regra de 'um grupo por papel': ciclo pode ter mais de um
        grupo de cartório, e os dois precisam do vínculo pra movimentar o processo."""
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])  # também vincula o SC do ator

        sc2 = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["SC"], nome="Grupo SC-2",
        )
        client = self.cliente_logado(self.usuarios["SC"])
        resp = client.post(
            reverse("processos:atribuir_grupo_processos"),
            data=json.dumps({"processo_ids": [processo.pk], "grupo_ids_adicionar": [sc2.pk]}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        nomes_sc = sorted(
            GrupoProcesso.objects.filter(processo=processo, grupo__cargo_simulacao__cod="SC")
            .values_list("grupo__nome", flat=True)
        )
        self.assertEqual(nomes_sc, ["Grupo SC", "Grupo SC-2"])

    def test_aplicar_grupos_tipos_movimentacao_prebuscado_evita_select_repetido(self):
        """Regressão de performance: quem chama aplicar_grupos() em lote (um processo por
        iteração) pode pré-buscar os dois TipoMovimentacao possíveis e passar pronto —
        sem isso seria o mesmo SELECT repetido a cada processo do lote."""
        tipos_movimentacao = {
            t.nome_movimentacao: t
            for t in TipoMovimentacao.objects.select_related("efeito_status").filter(
                nome_movimentacao__in=[NOME_AUTUACAO, NOME_REDISTRIBUICAO]
            )
        }

        def grupo_apa_fresco():
            return list(
                GrupoTrabalho.objects.filter(pk=self.grupos["APA"].pk)
                .select_related("cargo_simulacao")
            )

        processo_sem_cache = self.criar_processo_protocolado()
        grupos_1 = grupo_apa_fresco()
        with CaptureQueriesContext(connection) as sem_cache:
            aplicar_grupos(
                processo_sem_cache, grupos_adicionar=grupos_1, grupos_remover=[],
                ator=self.usuarios["SC"], grupo_serventia=self.grupos["SC"],
            )

        processo_com_cache = self.criar_processo_protocolado()
        grupos_2 = grupo_apa_fresco()
        with CaptureQueriesContext(connection) as com_cache:
            aplicar_grupos(
                processo_com_cache, grupos_adicionar=grupos_2, grupos_remover=[],
                ator=self.usuarios["SC"], grupo_serventia=self.grupos["SC"],
                tipos_movimentacao=tipos_movimentacao,
            )

        self.assertEqual(len(sem_cache.captured_queries) - len(com_cache.captured_queries), 1)

    def test_pode_editar_processo_nao_confundido_com_pode_visualizar(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"], segredo_justica=True)
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertTrue(pode_visualizar_processo(self.usuarios["APA"], processo))
        self.assertFalse(pode_editar_processo(self.usuarios["APA"], processo))
