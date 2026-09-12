from __future__ import annotations

from movimentacoes.models import MovimentacaoProcessual
from movimentacoes.services import registrar_movimentacao

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class StatusAutomaticoTests(CenarioMovimentacoesTestCase):
    """Ponto 5 do mapa: status automático a partir do efeito_status do tipo."""

    def test_movimentacao_com_efeito_atualiza_status(self):
        processo = self.criar_processo_protocolado()
        self.assertEqual(processo.status_atual.nome_status, "Protocolado")
        registrar_movimentacao(
            processo=processo, autor=self.usuarios["SC"], tipo_movimentacao=self.tipo("Autuação e Distribuição"),
        )
        processo.refresh_from_db()
        self.assertEqual(processo.status_atual.nome_status, "Autuado")

    def test_movimentacao_sem_efeito_nao_altera_status(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        status_antes = processo.status_atual_id
        self.registrar(
            processo, "Juntada de Documentos", self.usuarios["APA"],
            grupo_processo=self.grupo_processo(processo, "APA"),
        )
        processo.refresh_from_db()
        self.assertEqual(processo.status_atual_id, status_antes)

    def test_cancelamento_sobre_movimentacao_com_efeito_nao_reverte_status(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        mov_autuacao = MovimentacaoProcessual.objects.get(
            processo=processo, tipo_movimento__nome_movimentacao="Autuação e Distribuição",
        )
        self.registrar(
            processo, "Cancelamento / Tornar Sem Efeito", self.usuarios["SC"],
            grupo_processo=self.grupo_processo(processo, "SC"), movimentacao_origem=mov_autuacao,
        )
        processo.refresh_from_db()
        self.assertEqual(processo.status_atual.nome_status, "Autuado")


class HooksEfeitoColateralTests(CenarioMovimentacoesTestCase):
    """Ponto 6 do mapa: etapa de efeitos colaterais existe e não quebra o fluxo."""

    def test_sem_efeito_colateral_nao_dispara_nada_e_nao_quebra(self):
        processo = self.criar_processo_protocolado()
        tipo = self.tipo("Juntada de Documentos")
        self.assertEqual(tipo.efeitos_colaterais.count(), 0)
        mov = registrar_movimentacao(processo=processo, autor=self.usuarios["APA"], tipo_movimentacao=tipo)
        self.assertIsNotNone(mov.pk)
