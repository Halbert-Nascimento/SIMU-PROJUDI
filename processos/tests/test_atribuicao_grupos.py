from __future__ import annotations

import html
import re
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from ciclos.models import CicloSimulacao, GrupoTrabalho
from movimentacoes.catalogo import NOME_AUTUACAO, NOME_REDISTRIBUICAO
from notificacoes.models import Notificacao, TipoNotificacao
from processos.models import GrupoProcesso, PoloProcessual
from processos.permissions import pode_atribuir_grupos
from processos.services import (
    EstadoInvalidoError,
    Natureza,
    aplicar_alteracoes,
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

    def test_grupo_de_papel_que_a_posicao_nao_aceita_e_recusado(self):
        """
        A guarda vive no serviço, não só no form: com o ChoiceField desativado num experimento,
        um grupo Juiz entrou no polo passivo sem nada reclamar.
        """
        processo = self.criar_processo_protocolado()
        estados = self.estados(processo)

        with self.assertRaises(EstadoInvalidoError):
            planejar_alteracoes(estados, {"polo_passivo": self.grupos["JZ"]})

        with self.assertRaises(EstadoInvalidoError):
            planejar_alteracoes(estados, {"juiz": self.grupos["APA"]})

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


class AplicacaoDeAlteracoesTests(CenarioMovimentacoesTestCase):
    """Escrita no banco e registro do evento nos autos."""

    def dono_do_polo(self, processo, tipo_polo):
        """O grupo dono das linhas daquele polo — e falha se as linhas divergirem entre si."""
        donos = set(
            PoloProcessual.objects
            .filter(processo=processo, tipo_polo=tipo_polo)
            .values_list("grupo_id", flat=True)
        )
        self.assertEqual(len(donos), 1, f"linhas do polo {tipo_polo} com donos divergentes")
        (grupo_id,) = donos
        return GrupoTrabalho.objects.get(pk=grupo_id) if grupo_id else None

    def vinculos(self, processo):
        return set(GrupoProcesso.objects.filter(processo=processo).values_list("pk", flat=True))

    def grupo_novo(self, cod, nome):
        return GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos[cod], nome=nome,
        )

    def test_atribuir_cria_vinculo_da_o_polo_e_autua(self):
        processo = self.criar_processo_protocolado()  # APA protocolou, polos ainda sem grupo

        plano, movimentacao = aplicar_alteracoes(
            processo, {"polo_passivo": self.grupos["APP"]}, ator=self.usuarios["SC"],
        )
        processo.refresh_from_db()

        self.assertTrue(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APP"]).exists()
        )
        self.assertEqual(self.dono_do_polo(processo, "Passivo"), self.grupos["APP"])
        # regularização: o polo ativo do protocolante era nulo e passa a ser dele
        self.assertEqual(self.dono_do_polo(processo, "Ativo"), self.grupos["APA"])
        self.assertEqual(processo.status_atual.nome_status, "Autuado")
        self.assertEqual(movimentacao.tipo_movimento.nome_movimentacao, NOME_AUTUACAO)
        self.assertFalse(plano.vazio)

    def test_substituir_troca_vinculo_e_polo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        apa_novo = self.grupo_novo("APA", "Grupo APA dois")

        _, movimentacao = aplicar_alteracoes(
            processo, {"polo_ativo": apa_novo}, ator=self.usuarios["SC"],
        )
        processo.refresh_from_db()

        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APA"]).exists()
        )
        self.assertTrue(GrupoProcesso.objects.filter(processo=processo, grupo=apa_novo).exists())
        self.assertEqual(self.dono_do_polo(processo, "Ativo"), apa_novo)
        self.assertEqual(movimentacao.tipo_movimento.nome_movimentacao, NOME_REDISTRIBUICAO)
        self.assertEqual(processo.status_atual.nome_status, "Autuado")

    def test_remover_apaga_vinculo_e_solta_o_polo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])

        aplicar_alteracoes(processo, {"polo_passivo": None}, ator=self.usuarios["SC"])

        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APP"]).exists()
        )
        self.assertIsNone(self.dono_do_polo(processo, "Passivo"))
        self.assertEqual(self.dono_do_polo(processo, "Ativo"), self.grupos["APA"])

    def test_mp_que_troca_de_posicao_preserva_a_ancora_do_vinculo(self):
        """
        O MP que passa de interveniente a titular continua no processo: o vínculo é o mesmo,
        só o polo muda. Apagar e recriar faria as movimentações dele perderem a âncora e a
        janela de correção fechar para sempre.
        """
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "MP"])
        vinculo_mp = GrupoProcesso.objects.get(processo=processo, grupo=self.grupos["MP"])
        movimentacao_do_mp = self.registrar(
            processo, "Juntada de Documentos", self.usuarios["MP"], grupo_processo=vinculo_mp,
        )

        aplicar_alteracoes(
            processo,
            {"polo_ativo": self.grupos["MP"], "ministerio_publico": None},
            ator=self.usuarios["SC"],
        )

        movimentacao_do_mp.refresh_from_db()
        self.assertEqual(movimentacao_do_mp.grupo_processo_id, vinculo_mp.pk)
        self.assertEqual(self.dono_do_polo(processo, "Ativo"), self.grupos["MP"])
        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APA"]).exists()
        )

    def test_plano_vazio_nao_grava_nem_registra(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        vinculos_antes = self.vinculos(processo)
        movimentacoes_antes = processo.movimentacoes.count()

        plano, movimentacao = aplicar_alteracoes(processo, {}, ator=self.usuarios["SC"])

        self.assertTrue(plano.vazio)
        self.assertIsNone(movimentacao)
        self.assertEqual(self.vinculos(processo), vinculos_antes)
        self.assertEqual(processo.movimentacoes.count(), movimentacoes_antes)

    def test_confirmar_sem_alteracao_em_protocolado_autua_e_da_o_polo(self):
        """
        O fluxo antigo autuava mesmo recebendo um grupo já vinculado. Barrar por "nada mudou"
        deixaria o processo preso em Protocolado, com o grupo que peticionou sem polo e sem
        nenhuma forma de autuá-lo pela tela.
        """
        processo = self.criar_processo_protocolado()  # APA protocolou, polos ainda sem grupo

        plano, movimentacao = aplicar_alteracoes(processo, {}, ator=self.usuarios["SC"])
        processo.refresh_from_db()

        self.assertTrue(plano.vazio)
        self.assertEqual(processo.status_atual.nome_status, "Autuado")
        self.assertEqual(movimentacao.tipo_movimento.nome_movimentacao, NOME_AUTUACAO)
        self.assertEqual(self.dono_do_polo(processo, "Ativo"), self.grupos["APA"])
        self.assertIn("sem alteração de grupos", movimentacao.descricao_evento)

    def test_protocolado_sem_ocupante_ao_final_nao_autua_mas_registra(self):
        processo = self.criar_processo_protocolado()

        plano, movimentacao = aplicar_alteracoes(
            processo, {"polo_ativo": None}, ator=self.usuarios["SC"],
        )
        processo.refresh_from_db()

        self.assertEqual(plano.ocupantes, ())
        self.assertEqual(processo.status_atual.nome_status, "Protocolado")
        self.assertEqual(movimentacao.tipo_movimento.nome_movimentacao, NOME_REDISTRIBUICAO)

    def test_notifica_quem_entra_e_quem_sai(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        apa_novo = self.grupo_novo("APA", "Grupo APA dois")
        aluno_novo = Usuario.objects.create_user(
            username="aluno.apa2", email="aluno.apa2@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
        )
        apa_novo.membros.add(aluno_novo)
        Notificacao.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            aplicar_alteracoes(processo, {"polo_ativo": apa_novo}, ator=self.usuarios["SC"])

        self.assertEqual(
            set(Notificacao.objects
                .filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO)
                .values_list("destinatario_id", flat=True)),
            {aluno_novo.pk},
        )
        self.assertEqual(
            set(Notificacao.objects
                .filter(tipo=TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO)
                .values_list("destinatario_id", flat=True)),
            {self.usuarios["APA"].pk},
        )

    def test_grupo_que_so_troca_de_posicao_nao_e_notificado_de_vinculo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "MP"])
        Notificacao.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            aplicar_alteracoes(
                processo,
                {"polo_ativo": self.grupos["MP"], "ministerio_publico": None},
                ator=self.usuarios["SC"],
            )

        vinculados = set(Notificacao.objects
                         .filter(tipo=TipoNotificacao.GRUPO_VINCULADO_PROCESSO)
                         .values_list("destinatario_id", flat=True))
        desvinculados = set(Notificacao.objects
                            .filter(tipo=TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO)
                            .values_list("destinatario_id", flat=True))

        self.assertNotIn(self.usuarios["MP"].pk, vinculados)
        self.assertNotIn(self.usuarios["MP"].pk, desvinculados)
        self.assertIn(self.usuarios["APA"].pk, desvinculados)

    def test_evento_ancorado_no_vinculo_da_serventia(self):
        processo = self.criar_processo_protocolado()

        _, movimentacao = aplicar_alteracoes(
            processo, {"juiz": self.grupos["JZ"]}, ator=self.usuarios["SC"],
        )

        self.assertEqual(movimentacao.grupo_processo.grupo, self.grupos["SC"])
        self.assertEqual(movimentacao.autor, self.usuarios["SC"])

    def test_estado_invalido_nao_grava_nada(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        app_extra = self.grupo_novo("APP", "Grupo APP fora")
        GrupoProcesso.objects.create(processo=processo, grupo=app_extra)
        vinculos_antes = self.vinculos(processo)
        movimentacoes_antes = processo.movimentacoes.count()

        with self.assertRaises(EstadoInvalidoError):
            aplicar_alteracoes(processo, {"juiz": self.grupos["JZ"]}, ator=self.usuarios["SC"])

        self.assertEqual(self.vinculos(processo), vinculos_antes)
        self.assertEqual(processo.movimentacoes.count(), movimentacoes_antes)

    def test_falha_ao_registrar_o_evento_desfaz_os_vinculos_e_os_polos(self):
        """
        Sem a transação, o processo ficaria com o vínculo já apagado e nenhum evento nos autos
        explicando a saída do grupo — estado que ninguém consegue reconstituir depois.
        """
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        vinculos_antes = self.vinculos(processo)

        with mock.patch(
            "processos.services.registrar_movimentacao", side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                aplicar_alteracoes(
                    processo, {"polo_passivo": None}, ator=self.usuarios["SC"],
                )

        self.assertEqual(self.vinculos(processo), vinculos_antes)
        self.assertEqual(self.dono_do_polo(processo, "Passivo"), self.grupos["APP"])

    def test_descricao_do_evento_e_a_do_plano(self):
        processo = self.criar_processo_protocolado()

        plano, movimentacao = aplicar_alteracoes(
            processo,
            {"polo_passivo": self.grupos["APP"], "juiz": self.grupos["JZ"]},
            ator=self.usuarios["SC"],
        )

        self.assertEqual(movimentacao.descricao_evento, descrever_alteracoes(plano))
        self.assertIn('Polo passivo: "Grupo APP" atribuído.', movimentacao.descricao_evento)
        self.assertIn('Juiz: "Grupo JZ" atribuído.', movimentacao.descricao_evento)


class TelaDeAtribuicaoTests(CenarioMovimentacoesTestCase):
    """A tela em si: dois passos, trava de concorrência e POST forjado."""

    def url(self, processo, **params):
        url = reverse("processos:atribuir_grupos", args=[processo.numero])
        if params:
            url += "?" + "&".join(f"{chave}={valor}" for chave, valor in params.items())
        return url

    def payload(self, processo, **escolhas):
        return self.payload_atribuicao(processo, **escolhas)

    def test_get_renderiza_as_quatro_posicoes(self):
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])

        resp = client.get(self.url(processo))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["passo"], 1)
        self.assertEqual(
            [estado.posicao.chave for estado in resp.context["estados"]],
            ["polo_ativo", "polo_passivo", "ministerio_publico", "juiz"],
        )
        self.assertContains(resp, "Polo ativo")

    def test_quem_nao_e_serventia_recebe_403(self):
        processo = self.criar_processo_protocolado()
        for cod in ("APA", "APP", "MP", "JZ"):
            with self.subTest(cargo=cod):
                client = self.cliente_logado(self.usuarios[cod])
                self.assertEqual(client.get(self.url(processo)).status_code, 403)

    def test_revisar_mostra_o_resumo_sem_gravar(self):
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])
        dados = self.payload(processo, polo_passivo=str(self.grupos["APP"].pk))
        dados["acao"] = "revisar"

        resp = client.post(self.url(processo), dados)
        processo.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["passo"], 2)
        self.assertEqual(len(resp.context["plano"].alteracoes), 1)
        self.assertEqual(resp.context["nome_evento"], NOME_AUTUACAO)
        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APP"]).exists()
        )
        self.assertEqual(processo.status_atual.nome_status, "Protocolado")

    def test_confirmar_grava_e_volta_para_o_processo(self):
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])
        dados = self.payload(processo, polo_passivo=str(self.grupos["APP"].pk))
        dados["acao"] = "confirmar"

        resp = client.post(self.url(processo), dados)
        processo.refresh_from_db()

        self.assertRedirects(
            resp, reverse("processos:visualizar_processo", args=[processo.numero]),
        )
        self.assertTrue(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APP"]).exists()
        )
        self.assertEqual(processo.status_atual.nome_status, "Autuado")

    def test_next_do_site_e_honrado_e_o_externo_ignorado(self):
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])
        lista = reverse("processos:pagina_aluno")

        dados = self.payload(processo, juiz=str(self.grupos["JZ"].pk))
        dados.update({"acao": "confirmar", "next": lista})
        self.assertRedirects(client.post(self.url(processo), dados), lista)

        dados = self.payload(processo, polo_passivo=str(self.grupos["APP"].pk))
        dados.update({"acao": "confirmar", "next": "https://exemplo.invalido/roubo"})
        self.assertRedirects(
            client.post(self.url(processo), dados),
            reverse("processos:visualizar_processo", args=[processo.numero]),
        )

    def test_voltar_e_ajustar_preserva_o_next_inteiro(self):
        """O `next` viaja como valor de query string: sem urlencode, o `&` o trunca."""
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])
        lista = reverse("processos:pagina_aluno") + "?numero=&classe=&situacao=1&page=2"

        dados = self.payload(processo, polo_passivo=str(self.grupos["APP"].pk))
        dados.update({"acao": "revisar", "next": lista})
        resumo = client.post(self.url(processo), dados)

        href = re.search(
            r'<a href="([^"]+)"[^>]*>Voltar e ajustar</a>', resumo.content.decode()
        )
        self.assertIsNotNone(href, "o link de voltar sumiu do passo 2")
        # o navegador desfaz o escape de HTML antes de pedir a URL
        volta = client.get(html.unescape(href.group(1)))

        self.assertEqual(volta.context["proximo"], lista)

    def test_estado_mudou_recusa_e_reabre_a_tela(self):
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])
        dados = self.payload(processo, polo_passivo=str(self.grupos["APP"].pk))
        dados["acao"] = "confirmar"
        # outro serventuário mexeu no processo depois de a tela ter sido montada
        GrupoProcesso.objects.create(processo=processo, grupo=self.grupos["JZ"])

        resp = client.post(self.url(processo), dados)

        self.assertRedirects(resp, self.url(processo))
        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APP"]).exists()
        )

    def test_conflito_sem_resolucao_e_recusado(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        app_extra = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["APP"], nome="Grupo APP fora",
        )
        GrupoProcesso.objects.create(processo=processo, grupo=app_extra)
        client = self.cliente_logado(self.usuarios["SC"])
        dados = self.payload(processo)  # nada escolhido para a posição em conflito
        dados["acao"] = "confirmar"

        resp = client.post(self.url(processo), dados)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            GrupoProcesso.objects.filter(processo=processo, grupo=app_extra).exists()
        )

    def test_post_forjado_com_grupo_de_outro_papel_e_recusado(self):
        processo = self.criar_processo_protocolado()
        client = self.cliente_logado(self.usuarios["SC"])
        dados = self.payload(processo, polo_passivo=str(self.grupos["JZ"].pk))
        dados["acao"] = "confirmar"

        resp = client.post(self.url(processo), dados)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["JZ"]).exists()
        )

    def test_post_forjado_com_mesmo_papel_em_duas_posicoes_e_recusado(self):
        processo = self.criar_processo_protocolado()
        mp_extra = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["MP"], nome="Grupo MP dois",
        )
        client = self.cliente_logado(self.usuarios["SC"])
        dados = self.payload(
            processo,
            polo_ativo=str(self.grupos["MP"].pk),
            ministerio_publico=str(mp_extra.pk),
        )
        dados["acao"] = "confirmar"

        resp = client.post(self.url(processo), dados)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            GrupoProcesso.objects.filter(processo=processo, grupo=mp_extra).exists()
        )

    def test_dropdown_do_processo_oferece_a_tela_so_para_a_serventia(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        url_processo = reverse("processos:visualizar_processo", args=[processo.numero])

        resp_sc = self.cliente_logado(self.usuarios["SC"]).get(url_processo)
        resp_apa = self.cliente_logado(self.usuarios["APA"]).get(url_processo)

        # a asserção é no link, não no rótulo: o texto também aparece em comentário do HTML
        self.assertContains(resp_sc, self.url(processo))
        self.assertNotContains(resp_apa, self.url(processo))


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
