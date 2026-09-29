from __future__ import annotations

from decimal import Decimal
from unittest import mock

from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.urls import reverse

from ..estrelas import nota_para_meias_estrelas
from ..models import FeedbackProfessor
from .cenario import CenarioAvaliacao


class PreservaNotaGravadaTests(CenarioAvaliacao):

    def url(self, movimentacao):
        return reverse("avaliacoes:avaliar", args=[movimentacao.pk])

    def avaliar(self, nota):
        movimentacao = self.nova_movimentacao()
        FeedbackProfessor.objects.create(
            movimentacao=movimentacao, professor=self.prof, comentario="x", nota=nota,
        )
        return movimentacao

    def nota_gravada(self, movimentacao):
        return FeedbackProfessor.objects.get(movimentacao=movimentacao).nota

    def test_post_sem_o_campo_estrelas_nao_apaga_a_nota(self):
        mov = self.avaliar(Decimal("8.00"))
        # formulário de antes da troca: mandava `nota`, não `estrelas`
        self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "nota": "8.5", "acao": "concluir"},
        )
        self.assertEqual(self.nota_gravada(mov), Decimal("8.00"))

    def test_chave_vazia_continua_significando_sem_nota(self):
        mov = self.avaliar(Decimal("8.00"))
        self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "estrelas": "", "acao": "concluir"},
        )
        self.assertIsNone(self.nota_gravada(mov))

    def test_tela_envia_a_chave_antes_dos_radios(self):
        html = self.cliente(self.prof).get(self.url(self.nova_movimentacao())).content.decode()
        oculto = html.index('<input type="hidden" name="estrelas" value="">')
        self.assertLess(oculto, html.index('id="estrelas-5"'))

    def test_estrela_inalterada_preserva_a_nota_antiga(self):
        mov = self.avaliar(Decimal("7.35"))
        self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "estrelas": "4", "acao": "concluir"},
        )
        self.assertEqual(self.nota_gravada(mov), Decimal("7.35"))

    def test_outra_estrela_grava_o_multiplo_de_dois(self):
        mov = self.avaliar(Decimal("7.35"))
        self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "estrelas": "5", "acao": "concluir"},
        )
        self.assertEqual(self.nota_gravada(mov), Decimal("10.00"))

    def test_nota_antiga_fora_da_faixa_nao_estoura_e_e_normalizada(self):
        mov = self.avaliar(Decimal("15.00"))
        resposta = self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "estrelas": "5", "acao": "concluir"},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.nota_gravada(mov), Decimal("10.00"))

    def test_post_sem_estrelas_nao_apaga_nota_fora_da_faixa(self):
        mov = self.avaliar(Decimal("15.00"))
        resposta = self.cliente(self.prof).post(
            self.url(mov), {"comentario": "x", "acao": "concluir"},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.nota_gravada(mov), Decimal("15.00"))

    def test_tela_oferece_o_botao_limpar(self):
        html = self.cliente(self.prof).get(self.url(self.nova_movimentacao())).content.decode()
        self.assertIn('onclick="limparEstrelas()"', html)
        self.assertIn("function limparEstrelas()", html)


class FaixaDaNotaTests(CenarioAvaliacao):

    def feedback(self, nota):
        return FeedbackProfessor(
            movimentacao=self.nova_movimentacao(), professor=self.prof,
            comentario="x", nota=nota,
        )

    def test_model_aceita_zero_dez_e_sem_nota(self):
        for nota in (None, Decimal("0"), Decimal("7.35"), Decimal("10.00")):
            self.feedback(nota).full_clean()

    def test_model_recusa_nota_fora_de_zero_a_dez(self):
        for nota in (Decimal("10.01"), Decimal("15.00"), Decimal("-0.01")):
            with self.assertRaises(ValidationError, msg=str(nota)) as erro:
                self.feedback(nota).full_clean()
            self.assertIn("nota", erro.exception.message_dict)

    def test_barra_de_progresso_tem_teto_de_cem_por_cento(self):
        # objects.create não chama clean(): é o dado que já está no banco
        FeedbackProfessor.objects.create(
            movimentacao=self.nova_movimentacao(), professor=self.prof,
            comentario="x", nota=Decimal("15.00"),
        )
        resposta = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas"))
        self.assertEqual(resposta.context["media_percentual"], 100)


    def test_media_tem_teto_de_cinco_estrelas_nas_duas_telas(self):
        for nota in ("12.00", "15.00"):
            FeedbackProfessor.objects.create(
                movimentacao=self.nova_movimentacao(), professor=self.prof,
                comentario="x", nota=Decimal(nota),
            )
        minhas_notas = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas"))
        self.assertEqual(minhas_notas.context["media_geral"], 5)
        avaliar = self.cliente(self.prof).get(
            reverse("avaliacoes:avaliar", args=[self.nova_movimentacao().pk]),
        )
        self.assertEqual(avaliar.context["media_notas"], 5)
        self.assertIn('aria-label="5 de 5 estrelas"', avaliar.content.decode())


class MediaEmMeiasEstrelasTests(SimpleTestCase):

    def test_media_fica_entre_zero_e_cinco(self):
        self.assertEqual(nota_para_meias_estrelas(Decimal("12")), 5)
        self.assertEqual(nota_para_meias_estrelas(Decimal("99.99")), 5)
        self.assertEqual(nota_para_meias_estrelas(Decimal("-1")), 0)

    def test_media_dentro_da_faixa_nao_muda(self):
        self.assertEqual(nota_para_meias_estrelas(Decimal("7")), 3.5)
        self.assertEqual(nota_para_meias_estrelas(Decimal("10")), 5)
        self.assertIsNone(nota_para_meias_estrelas(None))


class RenderizacaoDasEstrelasTests(CenarioAvaliacao):

    def test_cada_desenho_e_renderizado_uma_vez(self):
        for nota in ("8.00", "8.00", "8.00", "4.00", None):
            FeedbackProfessor.objects.create(
                movimentacao=self.nova_movimentacao(), professor=self.prof,
                comentario="x", nota=None if nota is None else Decimal(nota),
            )
        with mock.patch(
            "avaliacoes.views.render_to_string", wraps=render_to_string,
        ) as renderizacao:
            resposta = self.cliente(self.aluno).get(reverse("avaliacoes:minhas_notas"))
        self.assertEqual(renderizacao.call_count, 3)   # 4 estrelas, 2 estrelas, sem nota
        self.assertEqual(len(resposta.context["feedbacks_json"]), 5)
