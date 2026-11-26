"""
Dois defeitos antigos: o valor da causa era multiplicado por 100 a cada gravação
pela tela, e título de anexo acima do tamanho da coluna derrubava a requisição.
"""

from __future__ import annotations

import json
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from movimentacoes.models import DocumentoAnexado, MovimentacaoProcessual
from processos.models import ProcessoJudicial
from processos.tests.fixtures import CenarioMovimentacoesTestCase
from processos.utils import normalizar_valor_monetario

PDF_MINIMO = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
TITULO_LONGO = "T" * 151
TITULO_NO_LIMITE = "T" * 150


class NormalizarValorTests(SimpleTestCase):
    def test_formato_da_tela_e_formato_brasileiro(self):
        casos = {
            # o que o campo mascarado envia
            "15000.00": "15000.00",
            "0.05": "0.05",
            "999999999.99": "999999999.99",
            # digitado em formato brasileiro
            "1.234,56": "1234.56",
            "1234,5": "1234.5",
            "1.234": "1234",
            "1.234.567": "1234567",
            "1500": "1500",
            # requisição manual com sobra em volta
            " 1.234 ": "1234",
            "+1.234": "+1234",
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_valor_monetario(entrada), esperado)


class ValorDaCausaTests(CenarioMovimentacoesTestCase):
    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA"])

    def salvar(self, valor):
        return self.cliente_logado(self.usuarios["SC"]).post(
            reverse("processos:modificar_dados_processo", args=[self.processo.numero]),
            data=json.dumps(
                {
                    "vara_id": self.vara.pk,
                    "tipo_processo_id": self.tipo_processo.pk,
                    "classe_id": self.classe.pk,
                    "valor_causa": valor,
                }
            ),
            content_type="application/json",
        )

    def test_salvar_varias_vezes_o_valor_da_tela_nao_altera_o_valor(self):
        for _ in range(3):
            self.assertEqual(self.salvar("15000.00").status_code, 200)
            self.processo.refresh_from_db()
            self.assertEqual(str(self.processo.valor_causa), "15000.00")

    def test_formato_brasileiro_continua_aceito(self):
        self.assertEqual(self.salvar("1.234,56").status_code, 200)
        self.processo.refresh_from_db()
        self.assertEqual(str(self.processo.valor_causa), "1234.56")


class TituloDeAnexoTests(CenarioMovimentacoesTestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = override_settings(PRIVATE_STORAGE_ROOT=pasta.name)
        ajuste.enable()
        self.addCleanup(ajuste.disable)

    def cliente(self):
        cliente = self.cliente_logado(self.usuarios["APA"])
        cliente.raise_request_exception = False
        return cliente

    def arquivo(self, nome="peca.pdf"):
        return SimpleUploadedFile(nome, PDF_MINIMO, content_type="application/pdf")

    def cadastrar(self, titulo, arquivo=None):
        return self.cliente().post(
            reverse("processos:cadastrar_processo"),
            {
                "comarca": self.comarca.pk,
                "vara": self.vara.pk,
                "tipo_processo": self.tipo_processo.pk,
                "classe": self.classe.pk,
                "valor_causa": "10.00",
                "polo_ativo": [self.parte_autor.pk],
                "polo_passivo": [self.parte_reu.pk],
                "documentos": [arquivo or self.arquivo()],
                "documento_nomes": [titulo],
            },
        )

    def movimentar(self, **campos):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        antes = MovimentacaoProcessual.objects.count()
        resposta = self.cliente().post(
            reverse("movimentacoes:criar_movimentacao", args=[processo.numero]),
            {"tipo_movimento": self.tipo("Juntada de Documentos").pk, **campos},
        )
        return resposta, MovimentacaoProcessual.objects.count() - antes

    def test_cadastro_recusa_titulo_ou_nome_de_arquivo_longo(self):
        casos = (
            (TITULO_LONGO, None),
            # sem título, vale o nome do arquivo
            ("", self.arquivo("n" * 160 + ".pdf")),
        )
        for titulo, arquivo in casos:
            with self.subTest(titulo=len(titulo)):
                total = ProcessoJudicial.objects.count()
                resposta = self.cadastrar(titulo, arquivo)
                self.assertContains(resposta, "150 caracteres")
                self.assertEqual(ProcessoJudicial.objects.count(), total)

    def test_cadastro_aceita_titulo_no_limite(self):
        resposta = self.cadastrar(TITULO_NO_LIMITE)

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            DocumentoAnexado.objects.filter(titulo_arquivo=TITULO_NO_LIMITE).exists()
        )

    def test_movimentacao_recusa_titulo_longo_de_arquivo_e_do_editor(self):
        casos = (
            {"documentos": [self.arquivo()], "documento_nomes": [TITULO_LONGO]},
            {"editor_html": "<p>peça</p>", "editor_html_nome": TITULO_LONGO},
        )
        for campos in casos:
            with self.subTest(campos=sorted(campos)):
                if "documentos" in campos:
                    campos["documentos"] = [self.arquivo()]
                resposta, criadas = self.movimentar(**campos)
                self.assertContains(resposta, "150 caracteres")
                self.assertEqual(criadas, 0)

    def test_movimentacao_aceita_titulo_do_editor_no_limite(self):
        resposta, criadas = self.movimentar(
            editor_html="<p>peça</p>", editor_html_nome=TITULO_NO_LIMITE
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(criadas, 1)
