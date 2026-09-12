from __future__ import annotations

from django.urls import reverse

from movimentacoes.models import MovimentacaoProcessual
from processos.models import PoloProcessual
from processos.permissions import pode_visualizar_processo

from .fixtures import CenarioMovimentacoesTestCase


class ProtocoloAutuacaoTests(CenarioMovimentacoesTestCase):
    """Ponto 2 do mapa: protocolo livre + autuação com distribuição de polo (Tarefa 4)."""

    def _dados_protocolo(self):
        return {
            "comarca": self.comarca.pk,
            "vara": self.vara.pk,
            "tipo_processo": self.tipo_processo.pk,
            "classe": self.classe.pk,
            "valor_causa": "1000.00",
            "segredo_justica": "",
            "polo_ativo": [self.parte_autor.pk],
            "polo_passivo": [self.parte_reu.pk],
        }

    def test_qualquer_grupo_autenticado_protocola_sem_checagem_papel(self):
        for cod in ("SC", "APA", "APP", "MP", "JZ"):
            with self.subTest(cargo=cod):
                client = self.cliente_logado(self.usuarios[cod])
                resp = client.post(reverse("processos:cadastrar_processo"), self._dados_protocolo())
                self.assertEqual(resp.status_code, 302)

    def test_processo_protocolado_nao_aparece_para_quem_nao_e_autor_nem_privilegiado(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        self.assertFalse(pode_visualizar_processo(self.usuarios["JZ"], processo))

    def test_polo_processual_sem_grupo_apos_protocolo(self):
        processo = self.criar_processo_protocolado()
        grupos = list(PoloProcessual.objects.filter(processo=processo).values_list("grupo", flat=True))
        self.assertTrue(grupos and all(g is None for g in grupos))

    def test_somente_serventia_autua_ou_distribui(self):
        processo = self.criar_processo_protocolado()
        resp_apa = self.autuar_processo(processo, ["APA"], sc_user=self.usuarios["APA"])
        self.assertEqual(resp_apa.status_code, 403)
        resp_sc = self.autuar_processo(processo, ["APA"])
        self.assertEqual(resp_sc.status_code, 200)

    def test_status_muda_protocolado_depois_autuado(self):
        processo = self.criar_processo_protocolado()
        self.assertEqual(processo.status_atual.nome_status, "Protocolado")
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertEqual(processo.status_atual.nome_status, "Autuado")

    def test_autuacao_atribui_polo_automatico_por_cargo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP"])
        ativo = PoloProcessual.objects.get(processo=processo, tipo_polo="Ativo")
        passivo = PoloProcessual.objects.get(processo=processo, tipo_polo="Passivo")
        self.assertEqual(ativo.grupo_id, self.grupos["APA"].pk)
        self.assertEqual(passivo.grupo_id, self.grupos["APP"].pk)
        self.assertFalse(PoloProcessual.objects.filter(processo=processo, grupo=self.grupos["MP"]).exists())

    def test_atribuir_grupos_duas_vezes_nao_duplica_autuacao(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        self.autuar_processo(processo, ["MP"])
        count = MovimentacaoProcessual.objects.filter(
            processo=processo, tipo_movimento__nome_movimentacao="Autuação e Distribuição",
        ).count()
        self.assertEqual(count, 1)
