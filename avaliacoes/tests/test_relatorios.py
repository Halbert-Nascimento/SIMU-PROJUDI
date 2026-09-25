from __future__ import annotations

from decimal import Decimal

from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from avaliacoes.models import FeedbackProfessor
from avaliacoes.permissions import pode_avaliar_movimentacao
from avaliacoes.services import notas_por_aluno
from ciclos.models import CicloSimulacao, StatusCiclo
from processos.permissions import pode_visualizar_processo

from .cenario import PERFIL, CenarioAvaliacao, criar_usuario

URL_NOTAS = "avaliacoes:relatorio_notas"
URL_PENDENTES = "avaliacoes:avaliacoes_pendentes"


class CenarioRelatorios(CenarioAvaliacao):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.coordenador = criar_usuario("coord.relatorio", PERFIL.COORDENADOR)
        cls.admin = criar_usuario("admin.relatorio", PERFIL.ADMIN)

    def avaliar(self, movimentacao, nota, professor=None):
        return FeedbackProfessor.objects.create(
            movimentacao=movimentacao,
            professor=professor or self.prof,
            comentario="Comentário de teste",
            nota=None if nota is None else Decimal(nota),
        )

    def obter(self, usuario, nome_url, **params):
        return self.cliente(usuario).get(reverse(nome_url), params)


class AcessoAosRelatoriosTests(CenarioRelatorios):
    def test_anonimo_vai_para_o_login(self):
        for nome_url in (URL_NOTAS, URL_PENDENTES):
            with self.subTest(nome_url):
                resposta = Client().get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 302)

    def test_aluno_nao_acessa(self):
        for nome_url in (URL_NOTAS, URL_PENDENTES):
            with self.subTest(nome_url):
                self.assertEqual(self.obter(self.aluno, nome_url).status_code, 404)

    def test_admin_coordenador_e_professor_acessam(self):
        for usuario in (self.admin, self.coordenador, self.prof):
            for nome_url in (URL_NOTAS, URL_PENDENTES):
                with self.subTest(usuario=usuario.username, tela=nome_url):
                    self.assertEqual(self.obter(usuario, nome_url).status_code, 200)


class PainelAtalhosTests(CenarioRelatorios):
    def test_atalhos_levam_as_duas_telas_e_os_antigos_sairam(self):
        resposta = self.obter(self.admin, "acesso:painel_administrativo")
        self.assertContains(resposta, reverse(URL_NOTAS))
        self.assertContains(resposta, reverse(URL_PENDENTES))
        self.assertNotContains(resposta, "Distribuir")
        self.assertNotContains(resposta, "Agendar")


class RelatorioNotasTests(CenarioRelatorios):
    def test_linha_do_aluno_traz_contagens_e_media_em_estrelas(self):
        avaliada = self.nova_movimentacao()
        devolvida = self.nova_movimentacao()
        self.nova_movimentacao()  # sem feedback
        self.avaliar(avaliada, "8.00")
        self.avaliar(devolvida, None)

        [linha] = notas_por_aluno(CicloSimulacao.objects.filter(pk=self.ciclo.pk))

        self.assertEqual(linha["aluno"], self.aluno)
        self.assertEqual(linha["total_movimentacoes"], 3)
        self.assertEqual(linha["total_avaliadas"], 1)
        self.assertEqual(linha["estrelas"], 4)
        self.assertEqual(linha["faixa"], "ok")

    def test_faixa_da_linha_concorda_com_as_estrelas_desenhadas(self):
        # 4.90 e 6.90 são as médias x,45 de estrela: arredondar duas vezes as empurraria para cima
        casos = {
            "4.00": (2, "erro"), "4.90": (2, "erro"), "5.00": (3, "warn"),
            "6.90": (3, "warn"), "7.00": (4, "ok"), "8.00": (4, "ok"),
        }
        for nota, (estrelas, faixa) in casos.items():
            with self.subTest(nota=nota):
                movimentacao = self.nova_movimentacao()
                feedback = self.avaliar(movimentacao, nota)

                [linha] = notas_por_aluno(CicloSimulacao.objects.filter(pk=self.ciclo.pk))
                # limpa antes de comparar: uma asserção que falha não pode contaminar o caso seguinte
                feedback.delete()
                movimentacao.delete()

                self.assertEqual(linha["estrelas"], estrelas)
                self.assertEqual(linha["faixa"], faixa)

    def test_media_geral_arredonda_uma_vez_so(self):
        self.avaliar(self.nova_movimentacao(), "4.90")

        resposta = self.obter(self.admin, URL_NOTAS)

        self.assertEqual(resposta.context["media_geral_estrelas"], 2)

    def test_media_e_exibida_em_estrelas_e_nao_como_numero(self):
        self.avaliar(self.nova_movimentacao(), "7.00")

        resposta = self.obter(self.admin, URL_NOTAS)

        # linha da tabela e card de média geral: ambos desenham 3,5 como 4 estrelas
        self.assertContains(resposta, 'aria-label="4 de 5 estrelas"', count=2)
        self.assertNotContains(resposta, ">3,5<")
        self.assertNotContains(resposta, ">3.5<")

    def test_aluno_sem_nota_continua_com_a_etiqueta_sem_nota(self):
        self.nova_movimentacao()

        resposta = self.obter(self.admin, URL_NOTAS)

        self.assertContains(resposta, "Sem nota")
        self.assertNotContains(resposta, 'class="estrelas')

    def test_duas_avaliacoes_da_mesma_movimentacao_contam_uma_vez(self):
        movimentacao = self.nova_movimentacao()
        self.avaliar(movimentacao, "10.00")
        self.avaliar(movimentacao, "6.00", professor=self.coordenador)

        [linha] = notas_por_aluno(CicloSimulacao.objects.filter(pk=self.ciclo.pk))

        self.assertEqual(linha["total_movimentacoes"], 1)
        self.assertEqual(linha["total_avaliadas"], 1)
        self.assertEqual(linha["estrelas"], 4)

    def test_aluno_sem_movimentacao_aparece_sem_nota(self):
        [linha] = notas_por_aluno(CicloSimulacao.objects.filter(pk=self.ciclo.pk))

        self.assertEqual(linha["total_movimentacoes"], 0)
        self.assertIsNone(linha["estrelas"])
        self.assertEqual(linha["faixa"], "gray")

    def test_professor_so_ve_o_ciclo_que_coordena(self):
        self.assertContains(self.obter(self.prof, URL_NOTAS), self.aluno.username)
        self.assertNotContains(self.obter(self.prof_fora, URL_NOTAS), self.aluno.username)

    def test_admin_e_coordenador_veem_todos_os_ciclos(self):
        for usuario in (self.admin, self.coordenador):
            with self.subTest(usuario.username):
                self.assertContains(self.obter(usuario, URL_NOTAS), self.aluno.username)

    def test_filtro_por_ciclo_de_outro_professor_nao_vaza(self):
        resposta = self.obter(self.prof_fora, URL_NOTAS, ciclo=self.ciclo.pk)

        self.assertNotContains(resposta, self.aluno.username)
        self.assertContains(resposta, "Ciclo inválido para o seu perfil.")

    def test_filtro_por_ciclo_restringe_a_lista(self):
        outro = CicloSimulacao.objects.create(
            nome_edicao="Outro Ciclo", coordenador=self.prof, semestre=2, ano=2026,
            status=self.ciclo.status,
        )
        outro_aluno = criar_usuario("aluno.outro", PERFIL.ALUNO)
        outro.participantes.add(outro_aluno)

        resposta = self.obter(self.prof, URL_NOTAS, ciclo=outro.pk)

        self.assertContains(resposta, outro_aluno.username)
        self.assertNotContains(resposta, self.aluno.username)

    def test_consultas_nao_crescem_com_o_numero_de_alunos(self):
        def consultas():
            with CaptureQueriesContext(connection) as capturadas:
                self.obter(self.prof, URL_NOTAS)
            return len(capturadas)

        antes = consultas()
        for indice in range(4):
            aluno = criar_usuario(f"aluno.extra{indice}", PERFIL.ALUNO)
            self.ciclo.participantes.add(aluno)

        self.assertEqual(consultas(), antes)


class AvaliacoesPendentesTests(CenarioRelatorios):
    def numeros_listados(self, usuario, **params):
        resposta = self.obter(usuario, URL_PENDENTES, **params)
        return resposta, list(resposta.context["pendentes"])

    def test_movimentacao_sem_feedback_aparece_e_com_feedback_some(self):
        pendente = self.nova_movimentacao()
        avaliada = self.nova_movimentacao()
        self.avaliar(avaliada, "8.00")

        _, listadas = self.numeros_listados(self.prof)

        self.assertEqual(listadas, [pendente])

    def test_devolvida_nao_e_pendente(self):
        self.avaliar(self.nova_movimentacao(), None)

        _, listadas = self.numeros_listados(self.prof)

        self.assertEqual(listadas, [])

    def test_movimentacao_do_proprio_usuario_fica_de_fora(self):
        propria = self.nova_movimentacao()
        propria.autor = self.coordenador
        propria.save()

        _, listadas = self.numeros_listados(self.coordenador)
        _, listadas_do_admin = self.numeros_listados(self.admin)

        self.assertEqual(listadas, [])
        self.assertEqual(listadas_do_admin, [propria])

    def test_professor_de_fora_nao_ve_pendencias_do_ciclo(self):
        self.nova_movimentacao()

        _, listadas = self.numeros_listados(self.prof_fora)

        self.assertEqual(listadas, [])

    def test_so_ciclos_em_andamento(self):
        self.nova_movimentacao()
        self.ciclo.status = StatusCiclo.objects.get_or_create(nome_status="Finalizado")[0]
        self.ciclo.save()

        _, listadas = self.numeros_listados(self.prof)

        self.assertEqual(listadas, [])

    def test_lista_da_mais_antiga_para_a_mais_recente(self):
        primeira = self.nova_movimentacao()
        segunda = self.nova_movimentacao()

        _, listadas = self.numeros_listados(self.prof)

        self.assertEqual(listadas, [primeira, segunda])

    def test_toda_linha_listada_pode_ser_avaliada_e_vista_por_quem_lista(self):
        self.nova_movimentacao()
        self.nova_movimentacao()

        for usuario in (self.prof, self.coordenador, self.admin):
            with self.subTest(usuario.username):
                _, listadas = self.numeros_listados(usuario)
                self.assertTrue(listadas)
                for movimentacao in listadas:
                    self.assertTrue(pode_avaliar_movimentacao(usuario, movimentacao))
                    self.assertTrue(pode_visualizar_processo(usuario, movimentacao.processo))

    def test_botao_avaliar_aponta_para_a_tela_de_avaliacao(self):
        movimentacao = self.nova_movimentacao()

        resposta, _ = self.numeros_listados(self.prof)

        self.assertContains(resposta, reverse("avaliacoes:avaliar", args=[movimentacao.pk]))

    def test_filtro_por_ciclo_de_outro_professor_nao_vaza(self):
        self.nova_movimentacao()

        resposta, listadas = self.numeros_listados(self.prof_fora, ciclo=self.ciclo.pk)

        self.assertEqual(listadas, [])
        self.assertContains(resposta, "Ciclo inválido para o seu perfil.")

    def test_consultas_nao_crescem_com_o_numero_de_pendencias(self):
        self.nova_movimentacao()

        def consultas():
            with CaptureQueriesContext(connection) as capturadas:
                self.obter(self.prof, URL_PENDENTES)
            return len(capturadas)

        antes = consultas()
        for _ in range(5):
            self.nova_movimentacao()

        self.assertEqual(consultas(), antes)
