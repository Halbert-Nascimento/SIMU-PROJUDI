from __future__ import annotations

from movimentacoes.models import TipoMovimentacao
from movimentacoes.services import NOMES_TRANSVERSAIS, resolver_movimentacao_origem, tipos_com_janela_aberta

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class JanelaCorrecaoTests(CenarioMovimentacoesTestCase):
    """Ponto 4 do mapa: janela de Emenda/Retificação e bloqueio de duplicidade (services.py)."""

    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA", "APP", "JZ", "SC"])
        self.gp_apa = self.grupo_processo(self.processo, "APA")
        self.gp_jz = self.grupo_processo(self.processo, "JZ")
        self.gp_sc = self.grupo_processo(self.processo, "SC")
        self.registrar(self.processo, "Emenda da Inicial", self.usuarios["JZ"], grupo_processo=self.gp_jz)

    def test_emenda_retificacao_sem_controle_unicidade(self):
        mov1 = self.registrar(self.processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=self.gp_apa)
        origem, erro = resolver_movimentacao_origem(
            processo=self.processo, tipo_movimentacao=self.tipo("Emenda Apresentada"), grupo_processo=self.gp_apa,
            mov_origem_solicitada=mov1, confirma_correcao=False,
        )
        self.assertIsNone(erro)
        self.assertEqual(origem, mov1)

    def test_janela_fecha_quando_algo_passa_a_depender(self):
        # única pré-condição satisfeita de "Conclusão ao Juiz" é a Emenda Apresentada — garante que
        # resolver_antecedente_logico aponte pra ela (senão pegaria outra pré-condição mais recente).
        mov1 = self.registrar(self.processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=self.gp_apa)
        self.registrar(self.processo, "Conclusão ao Juiz", self.usuarios["SC"], grupo_processo=self.gp_sc)
        origem, erro = resolver_movimentacao_origem(
            processo=self.processo, tipo_movimentacao=self.tipo("Emenda Apresentada"), grupo_processo=self.gp_apa,
            mov_origem_solicitada=mov1, confirma_correcao=False,
        )
        self.assertIsNone(origem)
        self.assertIsNotNone(erro)

    def test_reenvio_dentro_da_janela_sem_toggle_recusado(self):
        self.registrar(self.processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=self.gp_apa)
        origem, erro = resolver_movimentacao_origem(
            processo=self.processo, tipo_movimentacao=self.tipo("Emenda Apresentada"), grupo_processo=self.gp_apa,
            mov_origem_solicitada=None, confirma_correcao=False,
        )
        self.assertIsNone(origem)
        self.assertIn("Já existe uma movimentação do tipo", erro)

    def test_reenvio_fora_da_janela_aceito_como_nova_ocorrencia_sem_toggle(self):
        self.registrar(self.processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=self.gp_apa)
        self.registrar(self.processo, "Conclusão ao Juiz", self.usuarios["SC"], grupo_processo=self.gp_sc)  # fecha a janela
        origem, erro = resolver_movimentacao_origem(
            processo=self.processo, tipo_movimentacao=self.tipo("Emenda Apresentada"), grupo_processo=self.gp_apa,
            mov_origem_solicitada=None, confirma_correcao=False,
        )
        self.assertIsNone(erro)
        self.assertIsNone(origem)

    def test_transversais_nunca_bloqueadas_por_janela(self):
        for nome in NOMES_TRANSVERSAIS:
            with self.subTest(tipo=nome):
                origem, erro = resolver_movimentacao_origem(
                    processo=self.processo, tipo_movimentacao=self.tipo(nome), grupo_processo=self.gp_apa,
                    mov_origem_solicitada=None, confirma_correcao=False,
                )
                self.assertIsNone(erro)

    def test_tipos_com_janela_aberta(self):
        tipo_emenda = self.tipo("Emenda Apresentada")
        tipos = TipoMovimentacao.objects.filter(pk=tipo_emenda.pk)
        self.assertEqual(tipos_com_janela_aberta(self.processo, self.gp_apa, tipos), set())
        self.registrar(self.processo, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=self.gp_apa)
        self.assertEqual(tipos_com_janela_aberta(self.processo, self.gp_apa, tipos), {tipo_emenda.pk})
