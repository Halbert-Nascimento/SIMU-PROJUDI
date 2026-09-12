from __future__ import annotations

import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from ciclos.models import GrupoTrabalho
from movimentacoes.models import DocumentoAnexado
from movimentacoes.permissions import grupo_processo_do_usuario
from processos.models import GrupoProcesso

from processos.tests.fixtures import CenarioMovimentacoesTestCase

PDF_MINIMO = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


class ExtrasMovimentacoesTests(CenarioMovimentacoesTestCase):
    """Testes adicionais de valor real, além do Ponto 9 literal do mapa."""

    def test_usuario_em_dois_grupos_do_mesmo_processo_resolve_deterministico(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        self.autuar_processo(processo, ["APA", "APP"])
        grupo_extra = GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos["APP"], nome="Grupo APP extra",
        )
        grupo_extra.membros.add(self.usuarios["APA"])
        processo.grupos.add(grupo_extra)

        primeiro = grupo_processo_do_usuario(self.usuarios["APA"], processo)
        segundo = grupo_processo_do_usuario(self.usuarios["APA"], processo)
        self.assertIsNotNone(primeiro)
        self.assertEqual(primeiro.pk, segundo.pk)

    def test_atribuir_grupos_processo_grupoprocesso_nao_duplica_linha(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        self.autuar_processo(processo, ["APA", "APP"])
        count = GrupoProcesso.objects.filter(processo=processo, grupo=self.grupos["APA"]).count()
        self.assertEqual(count, 1)

    def test_documento_anexado_criado_ao_registrar_movimentacao_com_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(PRIVATE_STORAGE_ROOT=tmp):
                processo = self.criar_processo_protocolado()
                self.autuar_processo(processo, ["APA", "APP"])
                client = self.cliente_logado(self.usuarios["APA"])
                arquivo = SimpleUploadedFile("comprovante.pdf", PDF_MINIMO, content_type="application/pdf")
                resp = client.post(
                    reverse("movimentacoes:criar_movimentacao", args=[processo.numero]),
                    {
                        "tipo_movimento": self.tipo("Juntada de Documentos").pk,
                        "descricao_evento": "Comprovante juntado.",
                        "documentos": [arquivo],
                        "documento_nomes": ["Comprovante"],
                    },
                )
                self.assertEqual(resp.status_code, 302)
                self.assertTrue(
                    DocumentoAnexado.objects.filter(
                        movimentacao__processo=processo, titulo_arquivo="Comprovante",
                    ).exists()
                )
