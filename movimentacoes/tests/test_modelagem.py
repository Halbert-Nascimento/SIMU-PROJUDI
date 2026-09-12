from __future__ import annotations

from movimentacoes.models import MovimentacaoProcessual
from movimentacoes.permissions import pode_praticar_movimentacao
from movimentacoes.services import registrar_movimentacao
from processos.models import PoloProcessual

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class ModelagemTecnicaTests(CenarioMovimentacoesTestCase):
    """Ponto 8 do mapa: papéis autorizados, pré-condição em OR, efeito_status, efeito colateral, polo, autoria."""

    def test_tipo_com_multiplos_papeis_disponivel_para_qualquer_um(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP"])
        tipo = self.tipo("Juntada de Documentos")
        for cod in ("APA", "APP", "MP"):
            with self.subTest(cargo=cod):
                self.assertTrue(pode_praticar_movimentacao(self.usuarios[cod], processo, tipo))

    def test_precondicao_em_ou_aceita_qualquer_uma(self):
        tipo = self.tipo("Conclusão ao Juiz")

        p1 = self.criar_processo_protocolado()
        self.autuar_processo(p1, ["APA", "APP"])
        gp_sc1 = self.grupo_processo(p1, "SC")
        self.registrar(p1, "Custas Recolhidas", self.usuarios["SC"], grupo_processo=gp_sc1)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["SC"], p1, tipo))

        p2 = self.criar_processo_protocolado()
        self.autuar_processo(p2, ["APA", "APP"])
        gp_sc2 = self.grupo_processo(p2, "SC")
        self.registrar(p2, "Custas Não Recolhidas", self.usuarios["SC"], grupo_processo=gp_sc2)
        self.registrar(p2, "Intima autor p/ custas", self.usuarios["SC"], grupo_processo=gp_sc2)
        self.registrar(p2, "Custas Pagas Após Intimação", self.usuarios["SC"], grupo_processo=gp_sc2)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["SC"], p2, tipo))

        p3 = self.criar_processo_protocolado()
        self.autuar_processo(p3, ["APA", "APP", "JZ"])
        gp_jz3 = self.grupo_processo(p3, "JZ")
        gp_apa3 = self.grupo_processo(p3, "APA")
        self.registrar(p3, "Emenda da Inicial", self.usuarios["JZ"], grupo_processo=gp_jz3)
        self.registrar(p3, "Emenda Apresentada", self.usuarios["APA"], grupo_processo=gp_apa3)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["SC"], p3, tipo))

    def test_efeito_status_nulo_nao_altera_preenchido_altera(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        status_antes_id = processo.status_atual_id

        tipo_nulo = self.tipo("Juntada de Documentos")
        self.assertIsNone(tipo_nulo.efeito_status_id)
        self.registrar(processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=self.grupo_processo(processo, "APA"))
        processo.refresh_from_db()
        self.assertEqual(processo.status_atual_id, status_antes_id)

        processo2 = self.criar_processo_protocolado()
        tipo_preenchido = self.tipo("Autuação e Distribuição")
        self.assertIsNotNone(tipo_preenchido.efeito_status_id)
        registrar_movimentacao(processo=processo2, autor=self.usuarios["SC"], tipo_movimentacao=tipo_preenchido)
        processo2.refresh_from_db()
        self.assertEqual(processo2.status_atual_id, tipo_preenchido.efeito_status_id)

    def test_multiplas_categorias_efeito_colateral_disparam_todas(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "JZ"])
        self.avancar_ate_audiencia_sem_acordo(processo)
        self.avancar_ate_publicacao_intimacao(processo)
        tipo = self.tipo("Publicação/Intimação das Partes")
        categorias = set(tipo.efeitos_colaterais.values_list("categoria", flat=True))
        self.assertEqual(categorias, {"notifica", "abre_prazo"})
        mov = MovimentacaoProcessual.objects.filter(processo=processo, tipo_movimento=tipo).order_by("-pk").first()
        self.assertEqual(mov.tipo_movimento.efeitos_colaterais.count(), 2)

    def test_polo_ativo_pos_autuacao_retorna_grupo_correto_e_nulo_antes(self):
        processo = self.criar_processo_protocolado()
        self.assertIsNone(PoloProcessual.objects.get(processo=processo, tipo_polo="Ativo").grupo_id)
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertEqual(PoloProcessual.objects.get(processo=processo, tipo_polo="Ativo").grupo_id, self.grupos["APA"].pk)

    def test_historico_registra_grupo_que_praticou_mesmo_apos_usuario_trocar_de_grupo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        gp_apa = self.grupo_processo(processo, "APA")
        mov = self.registrar(processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=gp_apa)
        self.grupos["APP"].membros.add(self.usuarios["APA"])
        mov.refresh_from_db()
        self.assertEqual(mov.grupo_processo_id, gp_apa.pk)
