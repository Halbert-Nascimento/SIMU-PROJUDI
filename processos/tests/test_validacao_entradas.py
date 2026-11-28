"""
Entrada inválida vira resposta clara (400, 404 ou mensagem no formulário), nunca 500.
"""

from __future__ import annotations

import json

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from movimentacoes.catalogo import NOME_AUTUACAO
from movimentacoes.models import TipoMovimentacao
from processos.models import (
    GrupoProcesso,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
)
from processos.tests.fixtures import CenarioMovimentacoesTestCase
from processos.utils import ler_json_objeto

CORPOS_QUE_NAO_SAO_OBJETO = (
    b"{",
    b"[1, 2]",
    b'"texto"',
    b"12",
    b"null",
    b"\xff\xfe",
    b"[" * 5000 + b"]" * 5000,
)


class LerJsonObjetoTests(SimpleTestCase):
    def test_formulario_ja_lido_pelo_csrf_nao_derruba_a_rota(self):
        requisicao = RequestFactory().post("/", data={"nome_razao": "x"})
        _ = requisicao.POST  # o CsrfViewMiddleware lê o formulário antes da view

        self.assertIsNone(ler_json_objeto(requisicao))


class _CenarioJson(CenarioMovimentacoesTestCase):
    def cliente(self, cod="SC"):
        cliente = self.cliente_logado(self.usuarios[cod])
        cliente.raise_request_exception = False
        return cliente

    def post_json(self, url, corpo, cod="SC"):
        if not isinstance(corpo, bytes):
            corpo = json.dumps(corpo)
        return self.cliente(cod).post(url, data=corpo, content_type="application/json")

    def assertRecusa(self, resposta, trecho, status=400):
        self.assertEqual(resposta.status_code, status)
        self.assertIn(trecho, resposta.json()["erro"])


class CriarParteTests(_CenarioJson):
    url = property(lambda self: reverse("processos:criar_parte"))

    def corpo(self, **trocas):
        return {
            "nome_razao": "Maria Souza",
            "cpf_cnpj": "123.456.789-00",
            "tipo_pessoa": "Física",
            **trocas,
        }

    def test_letras_do_cnpj_sao_gravadas_em_maiusculas(self):
        resposta = self.post_json(
            self.url,
            self.corpo(cpf_cnpj="12.abc.345/01de-35", tipo_pessoa="Jurídica"),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["cpf_cnpj"], "12.ABC.345/01DE-35")
        self.assertTrue(
            ParteFicticia.objects.filter(
                pk=resposta.json()["id"], cpf_cnpj__regex=r"^12\.ABC"
            ).exists()
        )

    def test_mesmo_documento_com_outra_pontuacao_ou_caixa_e_duplicado(self):
        pares = (
            ("12.345.678/0001-90", "12345678000190", "Jurídica"),
            ("98765432000199", "98.765.432/0001-99", "Jurídica"),
            ("12.ABC.345/01DE-35", "12abc34501de35", "Jurídica"),
            ("123.456.789-00", "12345678900", "Física"),
            ("98765432100", "987.654.321-00", "Física"),
        )
        for primeiro, segundo, tipo in pares:
            with self.subTest(segundo=segundo):
                self.post_json(
                    self.url, self.corpo(cpf_cnpj=primeiro, tipo_pessoa=tipo)
                )
                total = ParteFicticia.objects.count()

                resposta = self.post_json(
                    self.url, self.corpo(cpf_cnpj=segundo, tipo_pessoa=tipo)
                )

                self.assertRecusa(resposta, "Já existe uma parte")
                self.assertEqual(ParteFicticia.objects.count(), total)

    def test_documento_gravado_com_espacos_tambem_conta_como_duplicado(self):
        ParteFicticia.objects.filter(pk=self.parte_autor.pk).update(
            cpf_cnpj=" 111.111.111-11 "
        )

        self.assertRecusa(
            self.post_json(self.url, self.corpo(cpf_cnpj="11111111111")),
            "Já existe uma parte",
        )

    def test_documentos_nos_formatos_aceitos_sao_gravados_como_digitados(self):
        # sem dígito verificador: seeds e material de aula usam números fictícios
        casos = (
            ("123.456.789-00", "Física"),
            ("98765432100", "Física"),
            ("12.345.678/0001-90", "Jurídica"),
            ("98765432000199", "Jurídica"),
            ("12.ABC.345/01DE-35", "Jurídica"),
            ("12ABC34501DE36", "Jurídica"),
        )
        for documento, tipo in casos:
            with self.subTest(documento=documento):
                resposta = self.post_json(
                    self.url, self.corpo(cpf_cnpj=documento, tipo_pessoa=tipo)
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.json()["cpf_cnpj"], documento)

    def test_mensagens_que_ja_existiam(self):
        self.assertRecusa(
            self.post_json(self.url, self.corpo(nome_razao="   ")),
            "Preencha todos os campos.",
        )
        self.assertRecusa(
            self.post_json(self.url, self.corpo(tipo_pessoa="Alienígena")),
            "Tipo de pessoa inválido.",
        )
        self.assertRecusa(
            self.post_json(self.url, self.corpo(cpf_cnpj=self.parte_autor.cpf_cnpj)),
            "Já existe uma parte",
        )

    def test_corpo_que_nao_e_objeto_json(self):
        for corpo in CORPOS_QUE_NAO_SAO_OBJETO:
            with self.subTest(corpo=corpo):
                self.assertRecusa(self.post_json(self.url, corpo), "JSON inválido")

    def test_texto_que_o_banco_nao_grava_e_recusado(self):
        self.assertRecusa(
            self.post_json(self.url, self.corpo(nome_razao="ab\ud800")), "inválido"
        )

    def test_espacos_em_volta_do_tipo_continuam_aceitos(self):
        resposta = self.post_json(self.url, self.corpo(tipo_pessoa=" Física "))
        self.assertEqual(resposta.status_code, 200)
        self.assertRecusa(
            self.post_json(self.url, self.corpo(tipo_pessoa="   ")),
            "Preencha todos os campos.",
        )

    def test_campos_invalidos_sao_recusados(self):
        casos = (
            ({"nome_razao": 123}, "inválido"),
            ({"nome_razao": {"a": 1}}, "inválido"),
            ({"cpf_cnpj": 12345678900}, "inválido"),
            ({"nome_razao": "N" * 151}, "150"),
            ({"cpf_cnpj": "1" * 21}, "20"),
            ({"cpf_cnpj": "abc"}, "CPF inválido"),
            ({"cpf_cnpj": "123.456.789-0"}, "CPF inválido"),
            ({"cpf_cnpj": "１２３４５６７８９００"}, "CPF inválido"),
            ({"cpf_cnpj": "1234", "tipo_pessoa": "Jurídica"}, "CNPJ inválido"),
            ({"cpf_cnpj": "12.345.678/0001-90"}, "não corresponde"),
            ({"tipo_pessoa": "Jurídica"}, "não corresponde"),
        )
        total = ParteFicticia.objects.count()
        for trocas, trecho in casos:
            with self.subTest(trocas=trocas):
                self.assertRecusa(
                    self.post_json(self.url, self.corpo(**trocas)), trecho
                )
        self.assertEqual(ParteFicticia.objects.count(), total)


class AlterarParteTests(_CenarioJson):
    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA"])
        self.url = reverse("processos:alterar_parte", args=[self.processo.numero])

    def corpo(self, **trocas):
        return {
            "parte_id": self.parte_autor.pk,
            "nome_razao": "Nome Novo",
            "cpf_cnpj": self.parte_autor.cpf_cnpj,
            "tipo_pessoa": self.parte_autor.tipo_pessoa,
            **trocas,
        }

    def test_altera_nome_com_id_inteiro_ou_texto(self):
        for parte_id in (self.parte_autor.pk, str(self.parte_autor.pk)):
            with self.subTest(parte_id=parte_id):
                resposta = self.post_json(self.url, self.corpo(parte_id=parte_id))
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.json()["nome_razao"], "Nome Novo")

    def test_parte_antiga_fora_do_formato_permite_corrigir_o_nome(self):
        ParteFicticia.objects.filter(pk=self.parte_autor.pk).update(cpf_cnpj="ANTIGO-1")

        resposta = self.post_json(self.url, self.corpo(cpf_cnpj="ANTIGO-1"))

        self.assertEqual(resposta.status_code, 200)

    def test_parte_antiga_gravada_com_espacos_permite_corrigir_o_nome(self):
        for gravado in ("ANTIGO-1 ", " ANTIGO-1"):
            with self.subTest(gravado=gravado):
                ParteFicticia.objects.filter(pk=self.parte_autor.pk).update(
                    cpf_cnpj=gravado
                )

                resposta = self.post_json(self.url, self.corpo(cpf_cnpj=gravado))

                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.json()["nome_razao"], "Nome Novo")

    def _outra_parte(self, documento):
        return ParteFicticia.objects.create(
            nome_razao="Outra Parte",
            cpf_cnpj=documento,
            tipo_pessoa=ParteFicticia.TipoPessoa.FISICA,
        )

    def test_documento_de_outra_parte_com_outra_pontuacao_e_recusado(self):
        self._outra_parte("555.666.777-88")

        self.assertRecusa(
            self.post_json(self.url, self.corpo(cpf_cnpj="55566677788")),
            "Já existe outra parte",
        )

    def test_trocar_so_a_pontuacao_do_proprio_documento_e_permitido(self):
        resposta = self.post_json(self.url, self.corpo(cpf_cnpj="11111111111"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["cpf_cnpj"], "11111111111")

    def test_duplicata_antiga_permite_corrigir_o_nome(self):
        # pares que o sistema aceitou antes da checagem continuam editáveis
        self._outra_parte("11111111111")

        resposta = self.post_json(self.url, self.corpo())

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["nome_razao"], "Nome Novo")

    def test_mesmo_texto_de_duplicata_antiga_e_recusado_sem_erro_500(self):
        self._outra_parte("11111111111")

        self.assertRecusa(
            self.post_json(self.url, self.corpo(cpf_cnpj="11111111111")),
            "Já existe outra parte",
        )

    def test_letras_do_cnpj_alterado_sao_gravadas_em_maiusculas(self):
        resposta = self.post_json(
            self.url,
            self.corpo(cpf_cnpj="12.abc.345/01de-35", tipo_pessoa="Jurídica"),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["cpf_cnpj"], "12.ABC.345/01DE-35")

    def test_documento_alterado_passa_a_ser_validado(self):
        self.assertRecusa(
            self.post_json(self.url, self.corpo(cpf_cnpj="ANTIGO-2")), "CPF inválido"
        )
        self.assertRecusa(
            self.post_json(self.url, self.corpo(tipo_pessoa="Jurídica")),
            "não corresponde",
        )
        self.assertRecusa(
            self.post_json(
                self.url,
                self.corpo(cpf_cnpj=self.parte_reu.cpf_cnpj, tipo_pessoa="Jurídica"),
            ),
            "Já existe outra parte",
        )

    def test_entradas_que_antes_derrubavam_a_rota(self):
        for parte_id in ("abc", [1], {"a": 1}, "9" * 40, None):
            with self.subTest(parte_id=parte_id):
                self.assertRecusa(
                    self.post_json(self.url, self.corpo(parte_id=parte_id)),
                    "não figura",
                    status=404,
                )
        for corpo in CORPOS_QUE_NAO_SAO_OBJETO:
            with self.subTest(corpo=corpo):
                self.assertRecusa(self.post_json(self.url, corpo), "JSON inválido")
        self.assertRecusa(
            self.post_json(self.url, self.corpo(nome_razao="N" * 151)), "150"
        )
        self.assertRecusa(
            self.post_json(self.url, self.corpo(nome_razao=7)), "inválido"
        )


class ModificarDadosTests(_CenarioJson):
    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA"])
        self.url = reverse(
            "processos:modificar_dados_processo", args=[self.processo.numero]
        )

    def corpo(self, **trocas):
        return {
            "vara_id": str(self.vara.pk),
            "tipo_processo_id": self.tipo_processo.pk,
            "classe_id": self.classe.pk,
            "valor_causa": "1.234,56",
            "segredo_justica": False,
            **trocas,
        }

    def test_dados_validos_inclusive_no_limite(self):
        for valor, gravado in (
            ("1.234,56", "1234.56"),
            ("", "0.00"),
            ("9.999.999.999.999,99", "9999999999999.99"),
        ):
            with self.subTest(valor=valor):
                resposta = self.post_json(self.url, self.corpo(valor_causa=valor))
                self.assertEqual(resposta.status_code, 200)
                self.processo.refresh_from_db()
                self.assertEqual(str(self.processo.valor_causa), gravado)

    def test_ids_invalidos(self):
        for campo in ("vara_id", "tipo_processo_id", "classe_id"):
            for valor in ("abc", [1], {"a": 1}, "9" * 40):
                with self.subTest(campo=campo, valor=valor):
                    self.assertRecusa(
                        self.post_json(self.url, self.corpo(**{campo: valor})),
                        "Selecione vara, tipo e classe.",
                    )

    def test_valores_que_nao_cabem_no_campo(self):
        for valor in ("NaN", "Infinity", "sNaN", "10000000000000", "1e30", "abc"):
            with self.subTest(valor=valor):
                self.assertRecusa(
                    self.post_json(self.url, self.corpo(valor_causa=valor)),
                    "Valor da causa inválido.",
                )

    def test_expoente_negativo_gigante_vira_zero(self):
        # sem arredondar antes de gravar, o driver tenta escrever bilhões de casas
        resposta = self.post_json(
            self.url, self.corpo(valor_causa="1e-999999999999999")
        )

        self.assertEqual(resposta.status_code, 200)
        self.processo.refresh_from_db()
        self.assertEqual(str(self.processo.valor_causa), "0.00")

    def test_corpo_que_nao_e_objeto_json(self):
        for corpo in CORPOS_QUE_NAO_SAO_OBJETO:
            with self.subTest(corpo=corpo):
                self.assertRecusa(self.post_json(self.url, corpo), "JSON inválido")


class AtribuirGrupoTests(_CenarioJson):
    url = property(lambda self: reverse("processos:atribuir_grupo_processos"))

    def setUp(self):
        self.processo = self.criar_processo_protocolado()

    def corpo(self, **trocas):
        return {
            "processo_ids": [self.processo.pk],
            "grupo_ids_adicionar": [str(self.grupos["APA"].pk)],
            **trocas,
        }

    def test_ids_inteiros_ou_texto_continuam_valendo(self):
        resposta = self.post_json(self.url, self.corpo())

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["atualizados"], 1)

    def test_lista_nula_vale_como_vazia(self):
        resposta = self.post_json(self.url, self.corpo(grupo_ids_remover=None))

        self.assertEqual(resposta.status_code, 200)

    def test_listas_invalidas(self):
        for campo in ("processo_ids", "grupo_ids_adicionar", "grupo_ids_remover"):
            for valor in (["abc"], "12", 5, [True], [{"a": 1}], ["9" * 40], [-1]):
                with self.subTest(campo=campo, valor=valor):
                    self.assertRecusa(
                        self.post_json(self.url, self.corpo(**{campo: valor})),
                        "Seleção inválida",
                    )

    def test_corpo_que_nao_e_objeto_json(self):
        for corpo in CORPOS_QUE_NAO_SAO_OBJETO:
            with self.subTest(corpo=corpo):
                self.assertRecusa(self.post_json(self.url, corpo), "JSON inválido")

    def test_tipo_de_movimentacao_ausente_desfaz_o_lote_inteiro(self):
        # o mais novo é processado primeiro e daria certo; o outro precisa da Autuação
        distribuido = self.criar_processo_protocolado()
        self.autuar_processo(distribuido, ["APA"])
        TipoMovimentacao.objects.filter(nome_movimentacao=NOME_AUTUACAO).update(
            nome_movimentacao="Renomeada no teste"
        )
        lote = (distribuido, self.processo)
        antes = [p.movimentacoes.count() for p in lote]

        resposta = self.post_json(
            self.url,
            self.corpo(
                processo_ids=[p.pk for p in lote],
                grupo_ids_adicionar=[self.grupos["JZ"].pk],
            ),
        )

        self.assertRecusa(resposta, "Contate o administrador")
        self.assertFalse(
            GrupoProcesso.objects.filter(
                processo__in=lote, grupo=self.grupos["JZ"]
            ).exists()
        )
        self.assertEqual([p.movimentacoes.count() for p in lote], antes)


class CadastroDePartesTests(_CenarioJson):
    url = property(lambda self: reverse("processos:cadastrar_processo"))

    def corpo(self, **trocas):
        return {
            "comarca": self.comarca.pk,
            "vara": self.vara.pk,
            "tipo_processo": self.tipo_processo.pk,
            "classe": self.classe.pk,
            "valor_causa": "10.00",
            "polo_ativo": [self.parte_autor.pk],
            "polo_passivo": [self.parte_reu.pk],
            **trocas,
        }

    def test_id_de_parte_invalido_volta_ao_formulario(self):
        for campo in ("polo_ativo", "polo_passivo", "polo_terceiro"):
            for valor in ("abc", "999999999", "9" * 40, "-1"):
                with self.subTest(campo=campo, valor=valor):
                    total = ProcessoJudicial.objects.count()
                    resposta = self.cliente("APA").post(
                        self.url,
                        self.corpo(**{campo: [valor]}),
                    )
                    self.assertContains(resposta, "Parte selecionada inválida")
                    self.assertEqual(ProcessoJudicial.objects.count(), total)

    def test_partes_validas_sao_preservadas_ao_voltar(self):
        resposta = self.cliente("APA").post(self.url, self.corpo(polo_terceiro=["abc"]))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["polo_ativo_partes"], [self.parte_autor])
        self.assertEqual(resposta.context["polo_terceiro_partes"], [])

    def test_mesma_parte_repetida_no_polo_e_gravada_uma_vez(self):
        resposta = self.cliente("APA").post(
            self.url,
            self.corpo(polo_ativo=[self.parte_autor.pk, self.parte_autor.pk]),
        )

        self.assertEqual(resposta.status_code, 302)
        processo = ProcessoJudicial.objects.latest("pk")
        self.assertEqual(
            PoloProcessual.objects.filter(processo=processo, tipo_polo="Ativo").count(),
            1,
        )


class FiltrosDaAreaDoAlunoTests(_CenarioJson):
    def setUp(self):
        self.processo = self.criar_processo_protocolado()

    def test_filtro_nao_numerico_e_ignorado(self):
        url = reverse("processos:pagina_aluno")
        for consulta in ({"classe": "abc"}, {"situacao": "9" * 40}):
            with self.subTest(consulta=consulta):
                resposta = self.cliente("APA").get(url, consulta)
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.context["total_processos"], 1)

    def test_filtro_valido_continua_filtrando(self):
        resposta = self.cliente("APA").get(
            reverse("processos:pagina_aluno"), {"classe": self.classe.pk + 999}
        )

        self.assertEqual(resposta.context["total_processos"], 0)
