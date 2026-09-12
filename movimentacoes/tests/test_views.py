from __future__ import annotations

from django.urls import reverse

from movimentacoes.models import MovimentacaoProcessual
from movimentacoes.permissions import tipos_praticaveis

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class RotasMovimentacaoTests(CenarioMovimentacoesTestCase):
    """Ponto 7 do mapa (lado movimentações) + teste de rotas pedido na Tarefa 8."""

    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA", "APP", "JZ"])
        self.gp_apa = self.grupo_processo(self.processo, "APA")

    def test_criar_movimentacao_get_anonimo_redireciona_login(self):
        url = reverse("movimentacoes:criar_movimentacao", args=[self.processo.numero])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"next={url}", resp.url)

    def test_editar_movimentacao_get_anonimo_redireciona_login(self):
        mov = self.registrar(self.processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=self.gp_apa)
        url = reverse("movimentacoes:editar_movimentacao", args=[self.processo.numero, mov.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"next={url}", resp.url)

    def test_criar_movimentacao_get_autenticado_200(self):
        client = self.cliente_logado(self.usuarios["APA"])
        resp = client.get(reverse("movimentacoes:criar_movimentacao", args=[self.processo.numero]))
        self.assertEqual(resp.status_code, 200)

    def test_editar_movimentacao_get_autenticado_200(self):
        mov = self.registrar(self.processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=self.gp_apa)
        client = self.cliente_logado(self.usuarios["APA"])
        resp = client.get(reverse("movimentacoes:editar_movimentacao", args=[self.processo.numero, mov.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_criar_movimentacao_post_completo_cria_e_redireciona(self):
        client = self.cliente_logado(self.usuarios["APA"])
        tipo = self.tipo("Juntada de Documentos")
        resp = client.post(
            reverse("movimentacoes:criar_movimentacao", args=[self.processo.numero]),
            {"tipo_movimento": tipo.pk, "descricao_evento": "Documento juntado."},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(MovimentacaoProcessual.objects.filter(processo=self.processo, tipo_movimento=tipo).exists())

    def test_editar_movimentacao_post_cria_nova_versao_com_origem(self):
        self.autuar_processo(self.processo, ["JZ"])
        gp_jz = self.grupo_processo(self.processo, "JZ")
        self.registrar(self.processo, "Emenda da Inicial", self.usuarios["JZ"], grupo_processo=gp_jz)
        mov1 = self.registrar(self.processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=self.gp_apa)
        client = self.cliente_logado(self.usuarios["APA"])
        resp = client.post(
            reverse("movimentacoes:editar_movimentacao", args=[self.processo.numero, mov1.pk]),
            {"tipo_movimento": self.tipo("Emenda Apresentada").pk, "descricao_evento": "Correção"},
        )
        self.assertEqual(resp.status_code, 302)
        mov2 = MovimentacaoProcessual.objects.filter(
            processo=self.processo, tipo_movimento__nome_movimentacao="Emenda Apresentada",
        ).order_by("-pk").first()
        self.assertEqual(mov2.movimentacao_origem_id, mov1.pk)

    def test_lista_tipos_oferecida_reflete_papel_do_usuario(self):
        client = self.cliente_logado(self.usuarios["JZ"])
        resp = client.get(reverse("movimentacoes:criar_movimentacao", args=[self.processo.numero]))
        esperado = set(tipos_praticaveis(self.usuarios["JZ"], self.processo).values_list("pk", flat=True))
        obtido = set(resp.context["tipos_movimentacao"].values_list("pk", flat=True))
        self.assertEqual(obtido, esperado)
