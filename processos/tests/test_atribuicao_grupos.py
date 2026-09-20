from __future__ import annotations

from django.contrib.auth.models import AnonymousUser

from ciclos.models import CicloSimulacao, GrupoTrabalho
from processos.models import GrupoProcesso, PoloProcessual
from processos.permissions import pode_atribuir_grupos
from processos.services import (
    EstadoInvalidoError,
    Natureza,
    descrever_alteracoes,
    estado_posicoes_do_processo,
    planejar_alteracoes,
)
from usuarios.models import Usuario

from .fixtures import CenarioMovimentacoesTestCase


class EstadoDasPosicoesTests(CenarioMovimentacoesTestCase):
    """Leitura do estado das quatro posições de um processo."""

    def posicoes(self, processo):
        return {estado.posicao.chave: estado for estado in estado_posicoes_do_processo(processo)}

    def test_protocolado_mostra_a_posicao_de_quem_peticionou(self):
        """
        Regressão do achado 2: antes da autuação o grupo que peticionou está vinculado sem
        polo. Lido pelo polo, ele desapareceria e o polo ativo apareceria pendente.
        """
        processo = self.criar_processo_protocolado()  # APA protocola
        self.assertFalse(
            PoloProcessual.objects.filter(processo=processo, grupo__isnull=False).exists()
        )

        posicoes = self.posicoes(processo)

        self.assertEqual(posicoes["polo_ativo"].grupo, self.grupos["APA"])
        self.assertTrue(posicoes["polo_passivo"].pendente)
        self.assertTrue(posicoes["ministerio_publico"].pendente)
        self.assertTrue(posicoes["juiz"].pendente)

    def test_serventia_nao_aparece_em_posicao_nem_como_opcao(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        grupo_sc = self.grupos["SC"]
        self.assertTrue(GrupoProcesso.objects.filter(processo=processo, grupo=grupo_sc).exists())

        for estado in estado_posicoes_do_processo(processo):
            with self.subTest(posicao=estado.posicao.chave):
                self.assertNotIn(grupo_sc, estado.grupos_vinculados)
                self.assertNotIn(grupo_sc, estado.grupos_disponiveis)

    def test_apos_distribuir_cada_posicao_tem_seu_grupo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP", "JZ"])

        posicoes = self.posicoes(processo)

        self.assertEqual(posicoes["polo_ativo"].grupo, self.grupos["APA"])
        self.assertEqual(posicoes["polo_passivo"].grupo, self.grupos["APP"])
        self.assertEqual(posicoes["ministerio_publico"].grupo, self.grupos["MP"])
        self.assertEqual(posicoes["juiz"].grupo, self.grupos["JZ"])

    def test_mp_que_ocupa_o_polo_ativo_aparece_como_titular(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        self.autuar_processo(processo, ["MP", "APP", "JZ"])
        PoloProcessual.objects.filter(processo=processo, tipo_polo="Ativo").update(
            grupo=self.grupos["MP"],
        )

        posicoes = self.posicoes(processo)

        self.assertEqual(posicoes["polo_ativo"].grupo, self.grupos["MP"])
        self.assertTrue(posicoes["ministerio_publico"].pendente)

    def test_posicao_indisponivel_quando_o_ciclo_nao_tem_grupo_do_papel(self):
        processo = self.criar_processo_protocolado()
        self.grupos["JZ"].delete()

        juiz = self.posicoes(processo)["juiz"]

        self.assertTrue(juiz.indisponivel)
        self.assertEqual(juiz.opcoes, ())

    def test_grupo_ja_vinculado_nao_e_oferecido_como_opcao(self):
        processo = self.criar_processo_protocolado()

        polo_ativo = self.posicoes(processo)["polo_ativo"]

        self.assertIn(self.grupos["APA"], polo_ativo.grupos_disponiveis)
        self.assertNotIn(self.grupos["APA"], polo_ativo.opcoes)
        self.assertIn(self.grupos["MP"], polo_ativo.opcoes)

    def test_leitura_em_tres_consultas(self):
        """Regressão de N+1: o custo não cresce com o número de posições nem de grupos."""
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP", "JZ"])

        with self.assertNumQueries(3):
            estado_posicoes_do_processo(processo)

    def test_posicao_com_dois_grupos_fica_em_conflito(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        app_extra = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["APP"], nome="Grupo APP fora",
        )
        GrupoProcesso.objects.create(processo=processo, grupo=app_extra)

        polo_passivo = self.posicoes(processo)["polo_passivo"]

        self.assertTrue(polo_passivo.em_conflito)
        self.assertIsNone(polo_passivo.grupo)
        self.assertEqual(len(polo_passivo.grupos_vinculados), 2)


class PlanejamentoDeAlteracoesTests(CenarioMovimentacoesTestCase):
    """Diff entre o estado atual das posições e o desejado."""

    def estados(self, processo):
        return estado_posicoes_do_processo(processo)

    def test_atribuir_posicao_pendente(self):
        processo = self.criar_processo_protocolado()
        estados = self.estados(processo)

        plano = planejar_alteracoes(estados, {"polo_passivo": self.grupos["APP"]})

        self.assertEqual(len(plano.alteracoes), 1)
        alteracao = plano.alteracoes[0]
        self.assertEqual(alteracao.natureza, Natureza.ATRIBUICAO)
        self.assertEqual(alteracao.grupo_novo, self.grupos["APP"])
        self.assertEqual(plano.vinculos_a_criar, (self.grupos["APP"],))
        self.assertEqual(plano.vinculos_a_remover, ())
        self.assertEqual(plano.donos_de_polo["Passivo"], self.grupos["APP"])
        # o protocolante segue dono do polo ativo: confirmar é o que regulariza o polo nulo
        self.assertEqual(plano.donos_de_polo["Ativo"], self.grupos["APA"])

    def test_substituir_grupo_da_posicao(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        apa_novo = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["APA"], nome="Grupo APA dois",
        )

        plano = planejar_alteracoes(self.estados(processo), {"polo_ativo": apa_novo})

        self.assertEqual(len(plano.alteracoes), 1)
        alteracao = plano.alteracoes[0]
        self.assertEqual(alteracao.natureza, Natureza.SUBSTITUICAO)
        self.assertEqual(alteracao.grupo_anterior, self.grupos["APA"])
        self.assertEqual(alteracao.grupo_novo, apa_novo)
        self.assertEqual(plano.vinculos_a_criar, (apa_novo,))
        self.assertEqual(plano.vinculos_a_remover, (self.grupos["APA"],))
        self.assertEqual(plano.donos_de_polo["Ativo"], apa_novo)

    def test_remover_grupo_da_posicao(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "JZ"])

        plano = planejar_alteracoes(self.estados(processo), {"juiz": None})

        self.assertEqual(len(plano.alteracoes), 1)
        alteracao = plano.alteracoes[0]
        self.assertEqual(alteracao.natureza, Natureza.REMOCAO)
        self.assertEqual(alteracao.grupo_anterior, self.grupos["JZ"])
        self.assertEqual(plano.vinculos_a_remover, (self.grupos["JZ"],))
        self.assertEqual(plano.vinculos_a_criar, ())

    def test_plano_vazio_quando_nada_muda(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])

        plano = planejar_alteracoes(self.estados(processo), {})

        self.assertTrue(plano.vazio)
        self.assertEqual(plano.vinculos_a_criar, ())
        self.assertEqual(plano.vinculos_a_remover, ())

    def test_mp_que_troca_de_posicao_gera_uma_linha_so(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP"])

        plano = planejar_alteracoes(
            self.estados(processo),
            {"polo_ativo": self.grupos["MP"], "ministerio_publico": None},
        )

        naturezas = [alteracao.natureza for alteracao in plano.alteracoes]
        self.assertEqual(naturezas, [Natureza.MUDANCA_DE_POSICAO, Natureza.REMOCAO])
        mudanca = plano.alteracoes[0]
        self.assertEqual(mudanca.grupo_novo, self.grupos["MP"])
        self.assertEqual(mudanca.posicao_origem.chave, "ministerio_publico")
        self.assertEqual(mudanca.posicao.chave, "polo_ativo")
        # o MP continua no processo: só o APA sai
        self.assertEqual(plano.vinculos_a_remover, (self.grupos["APA"],))
        self.assertEqual(plano.vinculos_a_criar, ())
        self.assertEqual(plano.donos_de_polo["Ativo"], self.grupos["MP"])

    def test_mesmo_papel_em_duas_posicoes_e_recusado(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APP"])
        mp_extra = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["MP"], nome="Grupo MP dois",
        )
        estados = self.estados(processo)

        with self.subTest(caso="dois grupos do mesmo papel"):
            with self.assertRaises(EstadoInvalidoError):
                planejar_alteracoes(estados, {
                    "polo_ativo": self.grupos["MP"], "ministerio_publico": mp_extra,
                })

        with self.subTest(caso="mesmo grupo nas duas posições"):
            with self.assertRaises(EstadoInvalidoError):
                planejar_alteracoes(estados, {
                    "polo_ativo": self.grupos["MP"], "ministerio_publico": self.grupos["MP"],
                })

    def test_posicao_em_conflito_exige_resolucao_explicita(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        app_extra = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["APP"], nome="Grupo APP fora",
        )
        GrupoProcesso.objects.create(processo=processo, grupo=app_extra)
        estados = self.estados(processo)

        with self.assertRaises(EstadoInvalidoError):
            planejar_alteracoes(estados, {"juiz": self.grupos["JZ"]})

        plano = planejar_alteracoes(estados, {"polo_passivo": self.grupos["APP"]})

        self.assertEqual(plano.vinculos_a_remover, (app_extra,))
        self.assertEqual(
            [alteracao.natureza for alteracao in plano.alteracoes], [Natureza.REMOCAO],
        )


class DescricaoDasAlteracoesTests(CenarioMovimentacoesTestCase):
    """Texto que vai para os autos e que a tela mostra antes de gravar."""

    def test_descricao_nomeia_posicao_e_natureza_na_ordem_das_posicoes(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "JZ"])
        apa_novo = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["APA"], nome="Grupo APA dois",
        )

        plano = planejar_alteracoes(estado_posicoes_do_processo(processo), {
            "polo_ativo": apa_novo,
            "polo_passivo": self.grupos["APP"],
            "juiz": None,
        })

        self.assertEqual(
            descrever_alteracoes(plano),
            'Polo ativo: "Grupo APA" substituído por "Grupo APA dois". '
            'Polo passivo: "Grupo APP" atribuído. '
            'Juiz: "Grupo JZ" removido.',
        )

    def test_descricao_de_mudanca_de_posicao_nao_diz_removido(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["MP"])
        self.autuar_processo(processo, ["MP", "APP"])

        plano = planejar_alteracoes(estado_posicoes_do_processo(processo), {
            "polo_ativo": self.grupos["MP"], "ministerio_publico": None,
        })

        descricao = descrever_alteracoes(plano)
        self.assertEqual(
            descricao,
            '"Grupo MP" passa de Ministério Público (interveniente) para Polo ativo.',
        )
        self.assertNotIn("removido", descricao)

    def test_plano_vazio_descreve_nada(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])

        plano = planejar_alteracoes(estado_posicoes_do_processo(processo), {})

        self.assertEqual(descrever_alteracoes(plano), "")


class PodeAtribuirGruposTests(CenarioMovimentacoesTestCase):
    def test_serventia_do_ciclo_pode(self):
        processo = self.criar_processo_protocolado()
        self.assertTrue(pode_atribuir_grupos(self.usuarios["SC"], processo))

    def test_demais_papeis_nao_podem(self):
        processo = self.criar_processo_protocolado()
        for cod in ("APA", "APP", "MP", "JZ"):
            with self.subTest(cargo=cod):
                self.assertFalse(pode_atribuir_grupos(self.usuarios[cod], processo))

    def test_professor_coordenador_e_admin_nao_podem(self):
        """Quem pratica ato processual é o papel simulado, não a autoridade sobre o ciclo."""
        processo = self.criar_processo_protocolado()
        admin = Usuario.objects.create_user(
            username="admin.atribuicao", email="admin.atribuicao@teste.local",
            password="s3nha-teste", tipo_perfil_global=Usuario.TipoPerfilGlobal.ADMIN,
        )
        coordenador = Usuario.objects.create_user(
            username="coord.atribuicao", email="coord.atribuicao@teste.local",
            password="s3nha-teste", tipo_perfil_global=Usuario.TipoPerfilGlobal.COORDENADOR,
        )

        self.assertFalse(pode_atribuir_grupos(self.professor, processo))
        self.assertFalse(pode_atribuir_grupos(admin, processo))
        self.assertFalse(pode_atribuir_grupos(coordenador, processo))

    def test_serventia_de_outro_ciclo_nao_pode(self):
        processo = self.criar_processo_protocolado()
        outro_ciclo = CicloSimulacao.objects.create(
            nome_edicao="Outro Ciclo", coordenador=self.professor,
            semestre=2, ano=2026, status=self.status_andamento,
        )
        grupo_sc_alheio = GrupoTrabalho.objects.create(
            ciclo=outro_ciclo, cargo_simulacao=self.cargos["SC"], nome="Serventia alheia",
        )
        aluno_alheio = Usuario.objects.create_user(
            username="aluno.alheio", email="aluno.alheio@teste.local",
            password="s3nha-teste", tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
        )
        grupo_sc_alheio.membros.add(aluno_alheio)

        self.assertFalse(pode_atribuir_grupos(aluno_alheio, processo))

    def test_anonimo_nao_pode(self):
        processo = self.criar_processo_protocolado()
        self.assertFalse(pode_atribuir_grupos(AnonymousUser(), processo))
