from __future__ import annotations

from django.urls import reverse

from movimentacoes.models import MovimentacaoProcessual

from .fixtures import CenarioMovimentacoesTestCase


class RotasERegressaoTests(CenarioMovimentacoesTestCase):
    """Rotas/{% url %}/regressão pedidas explicitamente pela Tarefa 8."""

    def test_visualizar_processo_renderiza_sem_noreversematch(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        self.autuar_processo(processo, ["APA", "APP"])
        gp_apa = self.grupo_processo(processo, "APA")
        self.registrar(processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=gp_apa)

        # duas variações: pode_avaliar True (professor) e False (aluno) — cobre o
        # {% url 'avaliacoes:avaliar' %} condicional a pode_avaliar/autor_id.
        for usuario in (self.professor, self.usuarios["APA"]):
            with self.subTest(usuario=usuario.username):
                client = self.cliente_logado(usuario)
                resp = client.get(reverse("processos:visualizar_processo", args=[processo.numero]))
                self.assertEqual(resp.status_code, 200)

    def test_movimentar_processo_renderiza_sem_noreversematch(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "JZ"])
        gp_apa = self.grupo_processo(processo, "APA")
        gp_jz = self.grupo_processo(processo, "JZ")
        self.registrar(processo, "Emenda da Inicial", self.usuarios["JZ"], grupo_processo=gp_jz)
        self.registrar(processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=gp_apa)

        # com tipo de janela aberta (APA) e sem nenhum (APP) — cobre o bloco condicional do toggle
        client_apa = self.cliente_logado(self.usuarios["APA"])
        resp_apa = client_apa.get(reverse("movimentacoes:criar_movimentacao", args=[processo.numero]))
        self.assertEqual(resp_apa.status_code, 200)

        client_app = self.cliente_logado(self.usuarios["APP"])
        resp_app = client_app.get(reverse("movimentacoes:criar_movimentacao", args=[processo.numero]))
        self.assertEqual(resp_app.status_code, 200)

    def test_regressao_processo_legado_pre_tarefa_0(self):
        """Movimentação criada direto via ORM (sem passar por registrar_movimentacao), como uma
        linha herdada de antes das Tarefas 3/4, continua aparecendo corretamente no histórico."""
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        MovimentacaoProcessual.objects.create(
            processo=processo, autor=self.usuarios["APA"], tipo_movimento=self.tipo("Juntada de Documentos"),
            descricao_evento="Movimentação legada.",
        )
        client = self.cliente_logado(self.usuarios["APA"])
        resp = client.get(reverse("processos:visualizar_processo", args=[processo.numero]))
        self.assertEqual(resp.status_code, 200)
        nomes = [m["nome"] for m in resp.context["movimentacoes"]]
        self.assertIn("Juntada de Documentos", nomes)
