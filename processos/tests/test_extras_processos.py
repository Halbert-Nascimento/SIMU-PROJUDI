from __future__ import annotations

from django.urls import reverse

from processos.models import PoloProcessual
from processos.permissions import pode_editar_processo, pode_visualizar_processo

from .fixtures import CenarioMovimentacoesTestCase


class ExtrasProcessosTests(CenarioMovimentacoesTestCase):
    """Testes adicionais de valor real, além do Ponto 9 literal do mapa."""

    def test_remover_grupos_das_posicoes_zera_o_polo(self):
        """
        Zerar deixou de ser uma ação única: cada posição é removida por si. O vínculo da
        serventia permanece de propósito — é ele que ancora os eventos nos autos.
        """
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        dados = self.payload_atribuicao(processo, polo_ativo="remover", polo_passivo="remover")
        dados["acao"] = "confirmar"

        client = self.cliente_logado(self.usuarios["SC"])
        client.post(reverse("processos:atribuir_grupos", args=[processo.numero]), dados)

        self.assertEqual(
            list(processo.grupos.values_list("cargo_simulacao__cod", flat=True)), ["SC"],
        )
        for polo in PoloProcessual.objects.filter(processo=processo):
            self.assertIsNone(polo.grupo_id)

    def test_pode_editar_processo_nao_confundido_com_pode_visualizar(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"], segredo_justica=True)
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertTrue(pode_visualizar_processo(self.usuarios["APA"], processo))
        self.assertFalse(pode_editar_processo(self.usuarios["APA"], processo))
