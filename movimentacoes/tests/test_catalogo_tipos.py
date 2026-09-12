from __future__ import annotations

from movimentacoes.models import MovimentacaoProcessual
from movimentacoes.permissions import pode_praticar_movimentacao
from processos.models import PoloProcessual

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class CatalogoTiposTests(CenarioMovimentacoesTestCase):
    """Ponto 3 do mapa: encadeamento lógico do catálogo."""

    def test_tipo_so_oferecido_com_precondicao_satisfeita(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "JZ"])
        self.assertFalse(pode_praticar_movimentacao(self.usuarios["APP"], processo, self.tipo("Contestação")))
        self.avancar_ate_audiencia_sem_acordo(processo)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["APP"], processo, self.tipo("Contestação")))

    def test_reabertura_prazo_decisao_embargos_libera_apelacao(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "JZ"])
        self.avancar_ate_audiencia_sem_acordo(processo)
        self.avancar_ate_publicacao_intimacao(processo)
        gp_app = self.grupo_processo(processo, "APP")
        gp_jz = self.grupo_processo(processo, "JZ")
        self.registrar(processo, "Embargos de Declaração", self.usuarios["APP"], grupo_processo=gp_app)
        self.registrar(processo, "Decisão nos Embargos", self.usuarios["JZ"], grupo_processo=gp_jz)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["APP"], processo, self.tipo("Apelação")))

    def test_transversais_referenciam_qualquer_movimentacao_anterior(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        gp_apa = self.grupo_processo(processo, "APA")
        antiga = self.registrar(processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=gp_apa)
        recente = self.registrar(processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=gp_apa)
        for alvo in (antiga, recente):
            with self.subTest(alvo=alvo.pk):
                mov = self.registrar(
                    processo, "Cancelamento / Tornar Sem Efeito", self.usuarios["SC"],
                    grupo_processo=self.grupo_processo(processo, "SC"), movimentacao_origem=alvo,
                )
                self.assertEqual(mov.movimentacao_origem_id, alvo.pk)

    def test_juntada_documentos_sem_precondicao_multiplas_vezes(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP"])
        gp_apa = self.grupo_processo(processo, "APA")
        for _ in range(3):
            self.assertTrue(pode_praticar_movimentacao(self.usuarios["APA"], processo, self.tipo("Juntada de Documentos")))
            self.registrar(processo, "Juntada de Documentos", self.usuarios["APA"], grupo_processo=gp_apa)
        count = MovimentacaoProcessual.objects.filter(
            processo=processo, tipo_movimento__nome_movimentacao="Juntada de Documentos",
        ).count()
        self.assertEqual(count, 3)

    def test_nenhuma_movimentacao_e_autorada_por_sistema(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        for mov in MovimentacaoProcessual.objects.filter(processo=processo):
            self.assertIsNotNone(mov.autor_id)

    def test_grupo_mp_protocola_e_nao_ocupa_polo_se_atribuido_na_autuacao(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        self.autuar_processo(processo, ["APA", "APP", "MP"])
        self.assertFalse(PoloProcessual.objects.filter(processo=processo, grupo=self.grupos["MP"]).exists())
        self.assertTrue(processo.grupos.filter(pk=self.grupos["MP"].pk).exists())

    def test_mp_pratica_movimentacoes_de_parte(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP", "JZ"])
        self.avancar_ate_audiencia_sem_acordo(processo)
        self.avancar_ate_publicacao_intimacao(processo)
        mp, jz = self.usuarios["MP"], self.usuarios["JZ"]
        gp_mp = self.grupo_processo(processo, "MP")
        # Apelação -> Contrarrazões -> Remessa/Julgamento/2º Grau -> Recurso Superior/REsp-RE:
        # cadeia só até aqui pra provar que o papel MP é aceito em cada elo, 2º grau em diante é fora de escopo.
        self.registrar(processo, "Apelação", mp, grupo_processo=gp_mp)
        self.registrar(processo, "Contrarrazões", mp, grupo_processo=gp_mp)
        self.registrar(processo, "Remessa ao 2º Grau", self.usuarios["SC"], grupo_processo=self.grupo_processo(processo, "SC"))
        self.registrar(processo, "Julgamento pelo Tribunal", jz)
        self.registrar(processo, "Recurso Provido", jz)
        self.registrar(processo, "Baixa dos Autos ao 1º Grau", jz)
        for nome in [
            "Réplica do Autor", "Memoriais/Alegações Finais", "Embargos de Declaração",
            "Apelação", "Contrarrazões", "Recurso Superior? (STJ/STF)",
        ]:
            with self.subTest(tipo=nome):
                self.assertTrue(pode_praticar_movimentacao(mp, processo, self.tipo(nome)))
        self.registrar(processo, "Recurso Superior? (STJ/STF)", mp, grupo_processo=gp_mp)
        self.assertTrue(pode_praticar_movimentacao(mp, processo, self.tipo("REsp/RE (STJ/STF)")))

    def test_mp_autor_bloqueia_mp_deve_intervir_sim(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        self.autuar_processo(processo, ["MP", "APP", "JZ"])
        # o polo ativo so nasce vinculado ao MP se o MP tiver protocolado — cenario raro, fora de escopo (Tarefa 4);
        # aqui simulamos diretamente o estado "MP ocupa o polo ativo" pra exercitar a condição 7 isoladamente.
        PoloProcessual.objects.filter(processo=processo, tipo_polo="Ativo").update(grupo=self.grupos["MP"])
        self.avancar_ate_audiencia_sem_acordo(processo)
        gp_app = self.grupo_processo(processo, "APP")
        self.registrar(processo, "Contestação", self.usuarios["APP"], grupo_processo=gp_app)
        self.registrar(processo, "Réplica do Autor", self.usuarios["APP"], grupo_processo=gp_app)
        self.assertFalse(pode_praticar_movimentacao(self.usuarios["JZ"], processo, self.tipo("MP Deve Intervir — Sim")))
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["JZ"], processo, self.tipo("MP Deve Intervir — Não")))

    def test_mp_nao_autor_permite_mp_deve_intervir_sim(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP", "JZ"])
        self.avancar_ate_audiencia_sem_acordo(processo)
        gp_app = self.grupo_processo(processo, "APP")
        self.registrar(processo, "Contestação", self.usuarios["APP"], grupo_processo=gp_app)
        self.registrar(processo, "Réplica do Autor", self.usuarios["APP"], grupo_processo=gp_app)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["JZ"], processo, self.tipo("MP Deve Intervir — Sim")))
