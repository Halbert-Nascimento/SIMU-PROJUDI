from __future__ import annotations

from processos.models import PoloProcessual
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

    def test_pode_editar_processo_nao_confundido_com_pode_visualizar(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"], segredo_justica=True)
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertTrue(pode_visualizar_processo(self.usuarios["APA"], processo))
        self.assertFalse(pode_editar_processo(self.usuarios["APA"], processo))
