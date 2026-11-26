"""
Guarda contra XSS nos scripts das telas processuais.

O projeto não tem runner de DOM, então a guarda é sobre o fonte: todo dado de
usuário interpolado em HTML montado no navegador passa por `escaparHtml`
(templates/static/js/escapar_html.js, coberto por scripts/teste_escapar_html.mjs).
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from processos.tests.fixtures import CenarioMovimentacoesTestCase

TELAS = {
    "processos/templates/processos/cadastro_processo.html": [
        "tipo",
        "comarcaTxt",
        "varaTxt",
        "classeTxt",
        "nome",
        "extra",
        "nomeDoc",
        "filename",
        "size",
        "parte.id",
        "parte.nome_razao",
        "parte.cpf_cnpj",
        "parte.tipo_pessoa",
        "p.nome_razao",
        "p.cpf_cnpj",
        "p.tipo_pessoa",
    ],
    "processos/templates/processos/visualizar_processo.html": [
        "v.id",
        "v.nome",
        "parte.polo",
        "parte.nome_razao",
    ],
    "movimentacoes/templates/movimentacoes/movimentar_processo.html": [
        "f.name",
        "f.title",
        "f.desc",
        "nome",
        "USUARIO_NOME",
    ],
}

# Seletor CSS e nome de campo recebem interpolação mas não viram HTML
FORA_DO_HTML = ("querySelector(", "const inputName")


def _fonte(caminho: str) -> str:
    return (Path(settings.BASE_DIR) / caminho).read_text(encoding="utf-8")


class EscapeNasTelasTests(CenarioMovimentacoesTestCase):
    def test_nenhum_dado_de_usuario_e_interpolado_sem_escape(self):
        for caminho, expressoes in TELAS.items():
            linhas = [
                linha
                for linha in _fonte(caminho).splitlines()
                if not any(marca in linha for marca in FORA_DO_HTML)
            ]
            fonte = "\n".join(linhas)
            for expressao in expressoes:
                with self.subTest(tela=Path(caminho).name, expressao=expressao):
                    cru = re.findall(
                        r"\$\{\s*" + re.escape(expressao) + r"\s*\}", fonte
                    )
                    self.assertEqual(cru, [])

    def test_telas_processuais_carregam_o_helper(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        cliente = self.cliente_logado(self.usuarios["APA"])
        rotas = (
            reverse("processos:cadastrar_processo"),
            reverse("processos:visualizar_processo", args=[processo.numero]),
            reverse("movimentacoes:criar_movimentacao", args=[processo.numero]),
        )
        for rota in rotas:
            with self.subTest(rota=rota):
                self.assertContains(cliente.get(rota), "js/escapar_html.js")

    def test_descricao_na_correcao_nao_vira_template_literal(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        grupo = self.grupo_processo(processo, "APA")
        movimentacao = self.registrar(
            processo,
            "Juntada de Documentos",
            self.usuarios["APA"],
            grupo_processo=grupo,
        )
        movimentacao.descricao_evento = "crase ` e ${window.__xss=1} fim"
        movimentacao.save(update_fields=["descricao_evento"])

        resposta = self.cliente_logado(self.usuarios["APA"]).get(
            reverse(
                "movimentacoes:editar_movimentacao",
                args=[processo.numero, movimentacao.pk],
            )
        )

        atribuicao = re.search(r"ta\.value = (.)(.*)\1;", resposta.content.decode())
        self.assertIsNotNone(atribuicao)
        self.assertEqual(atribuicao.group(1), "'")
        self.assertIn("${window.__xss", atribuicao.group(2))
