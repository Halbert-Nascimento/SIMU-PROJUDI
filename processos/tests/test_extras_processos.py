from __future__ import annotations

import json

from django.urls import reverse

from ciclos.models import GrupoTrabalho
from processos.models import GrupoProcesso, PoloProcessual
from processos.permissions import pode_editar_processo, pode_visualizar_processo

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

    def test_pode_editar_processo_nao_confundido_com_pode_visualizar(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"], segredo_justica=True)
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertTrue(pode_visualizar_processo(self.usuarios["APA"], processo))
        self.assertFalse(pode_editar_processo(self.usuarios["APA"], processo))
