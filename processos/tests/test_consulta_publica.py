"""
Consulta pública: o processo sem segredo continua aberto sem login, mas o
visitante não vê CPF/CNPJ completo nem alcança os anexos.
"""

from __future__ import annotations

from django.test import SimpleTestCase
from django.urls import reverse

from movimentacoes.models import DocumentoAnexado
from processos.models import ParteFicticia, PoloProcessual
from processos.tests.fixtures import CenarioMovimentacoesTestCase, aceite_termos_teste
from processos.utils import mascarar_cpf_cnpj
from usuarios.models import Usuario


class MascaraDeDocumentoTests(SimpleTestCase):
    def test_formatos(self):
        casos = {
            "123.456.789-00": "***.456.789-**",
            "12345678900": "***456789**",
            "12.345.678/0001-90": "**.345.678/****-**",
            "12345678000190": "**345678******",
            "12.ABC.345/01DE-35": "**.ABC.345/****-**",
            # fora dos dois tamanhos não há como saber o que é seguro mostrar
            "12345": "*****",
            "RG 1.234": "** *.***",
            "": "",
            None: "",
        }
        for documento, esperado in casos.items():
            with self.subTest(documento=documento):
                self.assertEqual(mascarar_cpf_cnpj(documento), esperado)


class _CenarioProcessoPublico(CenarioMovimentacoesTestCase):
    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA", "APP"])
        movimentacao = self.registrar(
            self.processo,
            "Juntada de Documentos",
            self.usuarios["APA"],
            grupo_processo=self.grupo_processo(self.processo, "APA"),
        )
        # caminho sem arquivo em disco: a autorização responde antes da leitura
        self.anexo = DocumentoAnexado.objects.create(
            movimentacao=movimentacao,
            titulo_arquivo="Anexo de consulta",
            caminho_arquivo=f"processos/{self.processo.numero}/ficticio.pdf",
        )
        self.url_processo = reverse(
            "processos:visualizar_processo", args=[self.processo.numero]
        )
        terceiro = ParteFicticia.objects.create(
            nome_razao="Terceira Interessada",
            cpf_cnpj="333.444.555-66",
            tipo_pessoa=ParteFicticia.TipoPessoa.FISICA,
        )
        PoloProcessual.objects.create(
            processo=self.processo,
            parte=terceiro,
            tipo_polo=PoloProcessual.TipoPolo.TERCEIRO,
        )
        # um documento por polo: cada bloco da tela aplica a máscara por conta própria
        self.documentos = (
            self.parte_autor.cpf_cnpj,
            self.parte_reu.cpf_cnpj,
            terceiro.cpf_cnpj,
        )


class VisitanteAnonimoTests(_CenarioProcessoPublico):
    def test_ve_o_processo_com_documento_mascarado(self):
        resposta = self.client.get(self.url_processo)

        self.assertEqual(resposta.status_code, 200)
        for documento in self.documentos:
            self.assertNotContains(resposta, documento)
            self.assertContains(resposta, mascarar_cpf_cnpj(documento))

    def test_ve_o_titulo_do_anexo_sem_link_para_o_arquivo(self):
        resposta = self.client.get(self.url_processo)

        self.assertContains(resposta, "Anexo de consulta")
        self.assertNotContains(resposta, self.anexo.caminho_arquivo.url)
        self.assertNotContains(resposta, "private-media")
        self.assertNotContains(resposta, "arq-btn visualizar")

    def test_nao_baixa_o_anexo_pelo_endereco_direto(self):
        resposta = self.client.get(self.anexo.caminho_arquivo.url)

        self.assertEqual(resposta.status_code, 403)


class UsuarioLogadoTests(_CenarioProcessoPublico):
    """Regressão: quem tem login vê exatamente o que via antes."""

    def leitores(self):
        admin = Usuario.objects.create_user(
            username="admin.consulta",
            email="admin.consulta@teste.local",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ADMIN,
            **aceite_termos_teste(),
        )
        # o MP não está vinculado: processo público continua aberto a qualquer logado
        return [self.usuarios["MP"], self.usuarios["APA"], self.professor, admin]

    def test_ve_documento_completo_e_links_do_anexo(self):
        for usuario in self.leitores():
            with self.subTest(usuario=usuario.username):
                resposta = self.cliente_logado(usuario).get(self.url_processo)
                for documento in self.documentos:
                    self.assertContains(resposta, documento)
                self.assertContains(resposta, self.anexo.caminho_arquivo.url)
                self.assertContains(resposta, "arq-btn baixar")

    def test_passa_pela_autorizacao_do_anexo(self):
        for usuario in self.leitores():
            with self.subTest(usuario=usuario.username):
                resposta = self.cliente_logado(usuario).get(
                    self.anexo.caminho_arquivo.url
                )
                # 404 é o arquivo fictício ausente; a recusa seria 403
                self.assertEqual(resposta.status_code, 404)

    def test_dados_para_o_modal_so_vao_para_quem_edita(self):
        editor = self.cliente_logado(self.usuarios["SC"]).get(self.url_processo)
        leitor = self.cliente_logado(self.usuarios["MP"]).get(self.url_processo)

        self.assertEqual(len(editor.context["partes_json"]), len(self.documentos))
        self.assertEqual(leitor.context["partes_json"], [])


class AnexoSigilosoTests(_CenarioProcessoPublico):
    def test_login_sem_vinculo_nao_baixa_anexo_de_processo_sigiloso(self):
        self.processo.segredo_justica = True
        self.processo.save(update_fields=["segredo_justica"])

        recusado = self.cliente_logado(self.usuarios["MP"])
        vinculado = self.cliente_logado(self.usuarios["APA"])
        url = self.anexo.caminho_arquivo.url

        self.assertEqual(recusado.get(url).status_code, 403)
        self.assertEqual(vinculado.get(url).status_code, 404)


class SigiloInalteradoTests(CenarioMovimentacoesTestCase):
    def test_segredo_e_protocolado_continuam_fechados_ao_visitante(self):
        protocolado = self.criar_processo_protocolado()
        sigiloso = self.criar_processo_protocolado(segredo_justica=True)
        self.autuar_processo(sigiloso, ["APA"])

        for processo in (protocolado, sigiloso):
            with self.subTest(processo=processo.numero):
                resposta = self.client.get(
                    reverse("processos:visualizar_processo", args=[processo.numero])
                )
                self.assertEqual(resposta.status_code, 403)
