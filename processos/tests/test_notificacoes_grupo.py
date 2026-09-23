from __future__ import annotations

from notificacoes.models import Notificacao, TipoNotificacao

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class NotificacaoGrupoVinculadoProcessoTests(CenarioMovimentacoesTestCase):
    """
    Notificação disparada em atribuir_grupo_processos() quando um grupo passa a
    estar vinculado a um processo (distribuição). O disparo real é via
    transaction.on_commit(), então cada chamada testada aqui precisa de
    captureOnCommitCallbacks() para os callbacks rodarem de verdade.

    Quem protocola aqui é o MP, nunca um dos grupos distribuídos: o grupo que protocola
    já entra vinculado ao processo (processos.views.cadastrar_processo) e a distribuição
    só notifica vínculo novo — com o APA protocolando, distribuir para o APA não
    notificaria ninguém e o teste mediria o silêncio.
    """

    def test_distribuir_notifica_grupos_recebidos_e_nao_o_sc_que_distribuiu(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, ["APA", "APP"])

        destinatarios = set(
            Notificacao.objects.filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO)
            .values_list("destinatario_id", flat=True)
        )
        self.assertEqual(destinatarios, {self.usuarios["APA"].pk, self.usuarios["APP"].pk})
        self.assertNotIn(self.usuarios["SC"].pk, destinatarios)

    def test_redistribuir_os_mesmos_grupos_nao_duplica_notificacao(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, ["APA", "APP"])
        primeira_contagem = Notificacao.objects.filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO).count()

        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, ["APA", "APP"])  # redistribuição, mesmos grupos

        self.assertEqual(
            Notificacao.objects.filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO).count(),
            primeira_contagem,
        )

    def test_distribuir_grupo_adicional_notifica_so_o_novo(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, ["APA"])
        Notificacao.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, ["APA", "APP"])  # inclui um grupo novo (APP)

        destinatarios = set(
            Notificacao.objects.filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO)
            .values_list("destinatario_id", flat=True)
        )
        self.assertEqual(destinatarios, {self.usuarios["APP"].pk})

    def test_mensagem_e_link_da_notificacao(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        with self.captureOnCommitCallbacks(execute=True):
            self.autuar_processo(processo, ["APA"])

        notificacao = Notificacao.objects.filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO).first()
        self.assertIn(processo.numero, notificacao.mensagem)
        self.assertEqual(notificacao.link_url, f"/processos/{processo.numero}/")
