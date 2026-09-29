from __future__ import annotations

from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from ..forms import FeedbackForm
from ..models import FeedbackProfessor
from .cenario import CenarioAvaliacao


class FormularioTests(CenarioAvaliacao):

    def formulario(self, **dados):
        return FeedbackForm(
            {"comentario": "Boa peça.", **dados}, ator=self.prof, movimentacao=self.nova_movimentacao(),
        )

    def test_aceita_de_uma_a_cinco_estrelas_e_grava_em_escala_interna(self):
        for estrelas, nota in ((1, "2.00"), (2, "4.00"), (3, "6.00"), (4, "8.00"), (5, "10.00")):
            form = self.formulario(estrelas=str(estrelas))
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data["nota"], Decimal(nota))

    def test_sem_estrelas_significa_sem_nota(self):
        form = self.formulario(estrelas="")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["nota"])

    def test_rejeita_zero_seis_texto_e_decimal(self):
        for invalido in ("0", "6", "-1", "abc", "3.5", "10"):
            form = self.formulario(estrelas=invalido)
            self.assertFalse(form.is_valid(), invalido)
            self.assertIn("Escolha de 1 a 5 estrelas.", form.errors["estrelas"], invalido)

    def test_reeditar_traz_a_estrela_da_nota_ja_gravada(self):
        feedback = FeedbackProfessor.objects.create(
            movimentacao=self.nova_movimentacao(), professor=self.prof,
            comentario="x", nota=Decimal("8.00"),
        )
        form = FeedbackForm(instance=feedback, ator=self.prof, movimentacao=feedback.movimentacao)
        self.assertEqual(form["estrelas"].value(), 4)

    def test_nota_antiga_fora_do_multiplo_de_dois_abre_na_estrela_mais_proxima(self):
        feedback = FeedbackProfessor.objects.create(
            movimentacao=self.nova_movimentacao(), professor=self.prof,
            comentario="x", nota=Decimal("7.35"),
        )
        form = FeedbackForm(instance=feedback, ator=self.prof, movimentacao=feedback.movimentacao)
        self.assertEqual(form["estrelas"].value(), 4)

    def test_permissao_continua_valendo(self):
        form = FeedbackForm(
            {"comentario": "x", "estrelas": "4"}, ator=self.prof_fora, movimentacao=self.nova_movimentacao(),
        )
        self.assertFalse(form.is_valid())


class AvaliarViewTests(CenarioAvaliacao):

    def url(self, movimentacao):
        return reverse("avaliacoes:avaliar", args=[movimentacao.pk])

    def test_concluir_com_quatro_estrelas_grava_oito(self):
        mov = self.nova_movimentacao()
        resposta = self.cliente(self.prof).post(
            self.url(mov), {"comentario": "Boa", "estrelas": "4", "acao": "concluir"},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(FeedbackProfessor.objects.get(movimentacao=mov).nota, Decimal("8.00"))

    def test_devolver_grava_sem_nota_mesmo_com_estrelas_marcadas(self):
        mov = self.nova_movimentacao()
        self.cliente(self.prof).post(
            self.url(mov), {"comentario": "Refaça", "estrelas": "5", "acao": "devolver"},
        )
        self.assertIsNone(FeedbackProfessor.objects.get(movimentacao=mov).nota)

    def test_estrelas_invalidas_nao_gravam_e_mostram_o_erro(self):
        mov = self.nova_movimentacao()
        resposta = self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "estrelas": "9", "acao": "concluir"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(FeedbackProfessor.objects.filter(movimentacao=mov).exists())

    def test_reavaliar_atualiza_o_mesmo_feedback(self):
        mov = self.nova_movimentacao()
        cliente = self.cliente(self.prof)
        cliente.post(self.url(mov), {"comentario": "a", "estrelas": "2", "acao": "concluir"})
        cliente.post(self.url(mov), {"comentario": "b", "estrelas": "5", "acao": "concluir"})
        self.assertEqual(FeedbackProfessor.objects.filter(movimentacao=mov).count(), 1)
        self.assertEqual(FeedbackProfessor.objects.get(movimentacao=mov).nota, Decimal("10.00"))

    def test_tela_mostra_o_seletor_com_a_estrela_gravada_marcada(self):
        mov = self.nova_movimentacao()
        FeedbackProfessor.objects.create(
            movimentacao=mov, professor=self.prof, comentario="x", nota=Decimal("6.00"),
        )
        html = self.cliente(self.prof).get(self.url(mov)).content.decode()
        self.assertIn('name="estrelas"', html)
        self.assertIn('id="estrelas-3" value="3" class="sr-only" checked', html)
        self.assertNotIn('id="estrelas-4" value="4" class="sr-only" checked', html)
        self.assertNotIn("0 a 10", html)

    def test_professor_de_fora_continua_sem_permissao(self):
        mov = self.nova_movimentacao()
        resposta = self.cliente(self.prof_fora).post(
            self.url(mov), {"comentario": "x", "estrelas": "4", "acao": "concluir"},
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(FeedbackProfessor.objects.exists())

    def test_historico_e_media_do_aluno_aparecem_em_estrelas(self):
        atual = self.nova_movimentacao()
        for nota in ("8.00", "6.00"):
            FeedbackProfessor.objects.create(
                movimentacao=self.nova_movimentacao(), professor=self.prof,
                comentario="x", nota=Decimal(nota),
            )
        html = self.cliente(self.prof).get(self.url(atual)).content.decode()
        # linhas do histórico (4★ e 3★) e a média (7,0 = 3,5★), todas pelo mesmo componente
        self.assertIn('aria-label="4 de 5 estrelas"', html)
        self.assertIn('aria-label="3 de 5 estrelas"', html)
        self.assertIn('aria-label="3,5 de 5 estrelas"', html)
        self.assertNotIn("de 5 estrelas</strong>", html)


class MinhasNotasViewTests(CenarioAvaliacao):

    def avaliar(self, nota):
        FeedbackProfessor.objects.create(
            movimentacao=self.nova_movimentacao(), professor=self.prof, comentario="x", nota=nota,
        )

    def test_aluno_ve_media_e_melhor_avaliacao_em_estrelas(self):
        self.avaliar(Decimal("10.00"))
        self.avaliar(Decimal("6.00"))
        resposta = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["media_geral"], 4)
        self.assertEqual(resposta.context["melhor_avaliacao"], 5)
        self.assertEqual(resposta.context["media_percentual"], 80)

    def test_media_com_meia_estrela_aparece_desenhada_nos_cards_e_nao_como_numero(self):
        self.avaliar(Decimal("8.00"))
        self.avaliar(Decimal("6.00"))
        resposta = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas"))
        html = resposta.content.decode()
        self.assertEqual(resposta.context["media_geral"], 3.5)
        self.assertEqual(resposta.context["media_percentual"], 70)
        self.assertIn('aria-label="3,5 de 5 estrelas"', html)
        self.assertIn("fa-star-half-stroke", html)
        self.assertNotIn(">3,5<", html)
        self.assertNotIn(">3.5<", html)

    def test_json_das_avaliacoes_traz_estrelas_faixa_e_html_pronto(self):
        self.avaliar(Decimal("8.00"))
        self.avaliar(Decimal("7.35"))   # nota antiga
        self.avaliar(None)              # devolvida
        dados = {a["estrelas"]: a for a in self.cliente(self.aluno).get(
            reverse("avaliacoes:minhas_notas")).context["feedbacks_json"] if a["estrelas"] is not None}
        self.assertEqual(sorted(dados), [4])          # 8,00 e 7,35 chegam ambas a 4 estrelas
        self.assertEqual(dados[4]["faixa"], "ok")
        self.assertIn('aria-label="4 de 5 estrelas"', dados[4]["estrelas_html"])
        semnota = [a for a in self.cliente(self.aluno).get(
            reverse("avaliacoes:minhas_notas")).context["feedbacks_json"] if a["estrelas"] is None]
        self.assertEqual(len(semnota), 1)
        self.assertEqual(semnota[0]["faixa"], "gray")

    def test_sem_avaliacao_nao_quebra(self):
        resposta = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.context["media_geral"])
        self.assertEqual(resposta.context["media_percentual"], 0)

    def test_tela_nao_fala_mais_em_nota_de_zero_a_dez(self):
        self.avaliar(Decimal("8.00"))
        html = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas")).content.decode()
        self.assertNotIn("10,00", html)
        self.assertIn("de 5 estrelas", html)


class SemMigrationTests(TestCase):
    """
    A avaliação em estrelas não pode alterar o schema: qualquer mudança no model
    geraria migration. Precisa das migrations reais no banco de teste — o
    autodetector compara com elas — e consulta `django_migrations`, por isso não
    é SimpleTestCase.
    """

    def test_nenhuma_migration_pendente(self):
        # SystemExit(1) se o autodetector encontrar qualquer mudança nos models
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)
