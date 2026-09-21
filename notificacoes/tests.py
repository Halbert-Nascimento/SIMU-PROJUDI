from __future__ import annotations

from django.urls import reverse

from notificacoes.models import Notificacao, TipoNotificacao
from notificacoes.services import notificar_movimentacao_registrada

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class NotificarMovimentacaoRegistradaTests(CenarioMovimentacoesTestCase):
    """Teste isolado do serviço, sem depender do hook em registrar_movimentacao()."""

    def test_cria_uma_notificacao_por_destinatario_e_retorna_a_lista_criada(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        mov = self.registrar(
            processo, "Juntada de Documentos", self.usuarios["APA"],
            grupo_processo=self.grupo_processo(processo, "APA"),
        )
        Notificacao.objects.all().delete()

        criadas = notificar_movimentacao_registrada(mov)

        self.assertEqual(len(criadas), 2)
        self.assertEqual(
            Notificacao.objects.filter(tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA).count(), 2,
        )

    def test_retorna_lista_vazia_sem_destinatarios(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        mov = processo.movimentacoes.get(tipo_movimento__nome_movimentacao="Protocolo da Petição Inicial")

        self.assertEqual(notificar_movimentacao_registrada(mov), [])


class RecentesNotificacoesViewTests(CenarioMovimentacoesTestCase):
    """
    notificacoes:recentes é o endpoint que o dropdown do sino busca ao abrir — busca
    o conteúdo atual e marca como lidas na mesma requisição (POST), numa única view,
    para o fragmento sempre refletir o `lida` de antes da marcação.
    """

    def test_retorna_fragmento_com_notificacoes_do_usuario_logado(self):
        destinatario = self.usuarios["APP"]
        Notificacao.objects.create(
            destinatario=destinatario, tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA,
            mensagem="Mensagem de teste do dropdown", link_url="/processos/1/",
        )
        client = self.cliente_logado(destinatario)

        resp = client.post(reverse("notificacoes:recentes"))

        self.assertContains(resp, "Mensagem de teste do dropdown")
        self.assertTemplateUsed(resp, "notificacoes/dropdown_conteudo.html")

    def test_nao_mistura_notificacao_de_outro_usuario(self):
        Notificacao.objects.create(
            destinatario=self.usuarios["APP"], tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA,
            mensagem="Não deveria aparecer para outro usuário", link_url="/processos/1/",
        )
        client = self.cliente_logado(self.usuarios["APA"])

        resp = client.post(reverse("notificacoes:recentes"))

        self.assertNotContains(resp, "Não deveria aparecer para outro usuário")

    def test_marca_como_lidas_apos_a_chamada(self):
        destinatario = self.usuarios["APP"]
        notificacao = Notificacao.objects.create(
            destinatario=destinatario, tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA,
            mensagem="Mensagem de teste do dropdown", link_url="/processos/1/",
        )
        client = self.cliente_logado(destinatario)

        client.post(reverse("notificacoes:recentes"))

        notificacao.refresh_from_db()
        self.assertTrue(notificacao.lida)
        self.assertIsNotNone(notificacao.data_leitura)
