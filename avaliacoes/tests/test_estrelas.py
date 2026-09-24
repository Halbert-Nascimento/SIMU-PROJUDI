from __future__ import annotations

from decimal import Decimal

from django.test import SimpleTestCase

from ..estrelas import (
    contexto_estrelas,
    estrelas_para_nota,
    faixa_da_estrela,
    faixa_da_media,
    media_em_estrelas,
    media_para_estrelas,
    nota_para_estrelas,
)


class EstrelasParaNotaTests(SimpleTestCase):

    def test_cada_estrela_vale_dois_pontos(self):
        self.assertEqual(
            [estrelas_para_nota(n) for n in range(1, 6)],
            [Decimal("2.00"), Decimal("4.00"), Decimal("6.00"), Decimal("8.00"), Decimal("10.00")],
        )

    def test_fora_de_um_a_cinco_e_erro(self):
        for invalido in (0, 6, -1):
            with self.assertRaises(ValueError, msg=invalido):
                estrelas_para_nota(invalido)


class NotaParaEstrelasTests(SimpleTestCase):

    def test_tabela_de_casos(self):
        casos = [
            (None, None),
            (Decimal("0"), 0),           # nota zero antiga: exibida como 0, sem forçar 1
            (Decimal("0.99"), 0),
            (Decimal("1.00"), 1),        # meio ponto sobe: 0,5 estrela -> 1
            (Decimal("2.00"), 1),
            (Decimal("2.99"), 1),
            (Decimal("3.00"), 2),        # 1,5 estrela -> 2
            (Decimal("3.99"), 2),
            (Decimal("4.00"), 2),
            (Decimal("6.00"), 3),
            (Decimal("7.35"), 4),        # nota antiga que não é múltipla de 2
            (Decimal("8.00"), 4),
            (Decimal("8.99"), 4),
            (Decimal("9.00"), 5),
            (Decimal("10.00"), 5),
        ]
        for nota, esperado in casos:
            self.assertEqual(nota_para_estrelas(nota), esperado, msg=f"nota={nota}")

    def test_aceita_float_e_texto_e_limita_a_cinco(self):
        self.assertEqual(nota_para_estrelas(8.0), 4)
        self.assertEqual(nota_para_estrelas("6.00"), 3)
        self.assertEqual(nota_para_estrelas(Decimal("99.99")), 5)

    def test_ida_e_volta_das_estrelas_validas(self):
        for n in range(1, 6):
            self.assertEqual(nota_para_estrelas(estrelas_para_nota(n)), n)


class MediaEFaixaTests(SimpleTestCase):

    def test_media_em_estrelas_tem_uma_casa(self):
        self.assertIsNone(media_em_estrelas(None))
        self.assertEqual(media_em_estrelas(Decimal("7.80")), 3.9)
        self.assertEqual(media_em_estrelas(Decimal("10")), 5.0)

    def test_faixas_usam_so_os_quatro_trios_do_guia(self):
        self.assertEqual(
            [faixa_da_estrela(n) for n in (None, 0, 1, 2, 3, 4, 5)],
            ["gray", "erro", "erro", "erro", "warn", "ok", "ok"],
        )

    def test_faixa_da_media_segue_as_estrelas_desenhadas(self):
        self.assertEqual(
            [faixa_da_media(m) for m in (None, 0.0, 2.4, 2.5, 3.0, 3.4, 3.5, 3.9, 4.0, 5.0)],
            ["gray", "erro", "erro", "warn", "warn", "warn", "ok", "ok", "ok", "ok"],
        )

    def test_media_de_sete_pontos_desenha_quatro_estrelas_e_pinta_como_quatro(self):
        media = media_em_estrelas(Decimal("7.00"))
        self.assertEqual(media, 3.5)
        self.assertEqual(media_para_estrelas(media), 4)
        self.assertEqual(faixa_da_media(media), "ok")

    def test_media_vira_estrela_inteira_com_meio_para_cima(self):
        self.assertEqual(
            [media_para_estrelas(m) for m in (None, 0.0, 2.4, 2.5, 3.5, 3.9, 4.4, 5.0)],
            [None, 0, 2, 3, 4, 4, 4, 5],
        )

    def test_contexto_das_estrelas(self):
        contexto = contexto_estrelas(3)
        self.assertEqual(contexto["itens"], [True, True, True, False, False])
        self.assertEqual(contexto["maximo"], 5)
        self.assertEqual(contexto_estrelas(None)["itens"], [False] * 5)
