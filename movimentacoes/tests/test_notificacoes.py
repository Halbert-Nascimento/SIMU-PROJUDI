from __future__ import annotations

from notificacoes.models import Notificacao, TipoNotificacao

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class NotificacaoMovimentacaoTests(CenarioMovimentacoesTestCase):
    """
    Notificação disparada em registrar_movimentacao() para os vinculados ao processo.
    O disparo real é via transaction.on_commit(), então cada chamada testada aqui
    precisa de captureOnCommitCallbacks() para os callbacks rodarem de verdade.
    """

    def test_notifica_membros_de_outros_grupos_vinculados_e_nao_o_autor(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        Notificacao.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            self.registrar(
                processo, "Juntada de Documentos", self.usuarios["APA"],
                grupo_processo=self.grupo_processo(processo, "APA"),
            )

        destinatarios = set(
            Notificacao.objects.filter(tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA)
            .values_list("destinatario_id", flat=True)
        )
        self.assertEqual(
            destinatarios,
            {self.usuarios["APP"].pk, self.usuarios["SC"].pk},
        )
        self.assertNotIn(self.usuarios["APA"].pk, destinatarios)

    def test_sem_outros_membros_vinculados_nao_cria_notificacao(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.criar_processo_protocolado(autor=self.usuarios["APA"])

        self.assertEqual(
            Notificacao.objects.filter(tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA).count(), 0,
        )

    def test_correcao_via_movimentacao_origem_tambem_notifica(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        gp_apa = self.grupo_processo(processo, "APA")
        with self.captureOnCommitCallbacks(execute=True):
            mov_original = self.registrar(
                processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=gp_apa,
            )
        Notificacao.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            self.registrar(
                processo, "Juntada de Documentos", self.usuarios["APA"],
                grupo_processo=gp_apa, movimentacao_origem=mov_original,
            )

        self.assertEqual(
            Notificacao.objects.filter(tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA).count(), 2,
        )

    def test_mensagem_e_link_da_notificacao(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        Notificacao.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            self.registrar(
                processo, "Juntada de Documentos", self.usuarios["APA"],
                grupo_processo=self.grupo_processo(processo, "APA"),
            )

        notificacao = Notificacao.objects.filter(tipo=TipoNotificacao.MOVIMENTACAO_REGISTRADA).first()
        self.assertIn(processo.numero, notificacao.mensagem)
        self.assertIn("Juntada de Documentos", notificacao.mensagem)
        self.assertEqual(notificacao.link_url, f"/processos/{processo.numero}/")
