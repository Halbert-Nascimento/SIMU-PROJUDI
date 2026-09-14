from __future__ import annotations

from django.urls import reverse

from processos.permissions import pode_visualizar_processo

from .fixtures import CenarioMovimentacoesTestCase


class VisualizacaoProcessoTests(CenarioMovimentacoesTestCase):
    """Ponto 7 do mapa (lado processos) + interações de pode_visualizar_processo."""

    def test_historico_exibe_tipo_real_sem_remendo_peticao_inicial(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        client = self.cliente_logado(self.usuarios["APA"])
        resp = client.get(reverse("processos:visualizar_processo", args=[processo.numero]))
        nomes = [m["nome"] for m in resp.context["movimentacoes"]]
        self.assertIn("Protocolo da Petição Inicial", nomes)
        self.assertNotIn("Petição Inicial", nomes)

    def test_segredo_justica_com_status_protocolado_bloqueia_publico(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"], segredo_justica=True)
        self.assertFalse(pode_visualizar_processo(self.usuarios["JZ"], processo))
        self.autuar_processo(processo, ["APA", "APP"])
        # segredo de justiça continua bloqueando mesmo depois de autuado — diferente do bloqueio por
        # status "Protocolado" (Tarefa 4), que se resolve sozinho assim que o processo é autuado.
        self.assertFalse(pode_visualizar_processo(self.usuarios["JZ"], processo))
