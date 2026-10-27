#!/usr/bin/env python
"""
Converte manual-usuario/MANUAL_DO_USUARIO.md em páginas HTML por capítulo.

    py -3.13 scripts/gerar_manual_html.py           # gera
    py -3.13 scripts/gerar_manual_html.py --check   # falha se o gerado estiver velho

Depende de `markdown-it-py` (extra `dev` do pyproject); o servidor não precisa
dele, porque o resultado é versionado em manual/.

Saídas:
  manual/templates/manual/capitulos/<slug>.html   corpo de cada capítulo
  manual/metadados.json                           versão, sumário de cada página
  manual/static/manual/busca.json                 índice da busca no navegador
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from manual.capitulos import CAPITULOS  # noqa: E402

ORIGEM = RAIZ / "manual-usuario" / "MANUAL_DO_USUARIO.md"
IMAGENS = RAIZ / "manual-usuario" / "assets"
DESTINO_CAPITULOS = RAIZ / "manual" / "templates" / "manual" / "capitulos"
DESTINO_METADADOS = RAIZ / "manual" / "metadados.json"
DESTINO_BUSCA = RAIZ / "manual" / "static" / "manual" / "busca.json"

SECOES_DESCARTADAS = {"Índice"}
AVISOS = {"⚠": "atencao", "ℹ": "neutro", "🔒": "neutro"}
MARCADOR_ANCORA = re.compile(r"^<a name=\"([^\"]+)\"></a>\s*$")
MARCADOR_TEXTO = re.compile(r"^@@ANCORA:([^@]+)@@$")
LIMITE_TEXTO_BUSCA = 1500
# páginas geradas pelo sistema: o manual aponta para elas pelo slug, sem âncora interna
DINAMICOS = {c.slug for c in CAPITULOS if not c.secoes}


def slug_titulo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto.lower())
    return re.sub(r"\s+", "-", texto.strip())


def dividir_secoes(markdown: str) -> tuple[dict[str, str], dict[str, str]]:
    """Separa o cabeçalho (H1 e versão) das seções H2, devolvendo cada uma com sua âncora de abertura."""
    linhas = markdown.splitlines()
    cabecalho, secoes, atual, titulo = [], {}, None, None
    for linha in linhas:
        if linha.startswith("## "):
            titulo = linha[3:].strip()
            atual = secoes.setdefault(titulo, [])
            atual.append(linha)
        elif atual is None:
            cabecalho.append(linha)
        else:
            atual.append(linha)

    # a âncora de uma seção fica no fim da anterior; ela precisa voltar para o começo da própria seção
    titulos = list(secoes)
    for anterior, seguinte in zip(titulos, titulos[1:]):
        cauda = secoes[anterior]
        orfas = []
        while cauda and (not cauda[-1].strip() or cauda[-1].strip() == "---" or MARCADOR_ANCORA.match(cauda[-1])):
            ultima = cauda.pop()
            if MARCADOR_ANCORA.match(ultima):
                orfas.insert(0, ultima)
        secoes[seguinte] = orfas + secoes[seguinte]
    while secoes[titulos[-1]] and secoes[titulos[-1]][-1].strip() in ("", "---"):
        secoes[titulos[-1]].pop()

    meta = {}
    for linha in cabecalho:
        achado = re.match(r"\*\*(Versão|Última atualização):\*\*\s*(.+)", linha)
        if achado:
            meta[achado.group(1)] = achado.group(2).strip()
    return {t: "\n".join(l) for t, l in secoes.items()}, meta


def preparar_ancoras(texto: str) -> str:
    # `<a name>` colado no título viraria um bloco HTML que engole a linha seguinte
    saida = []
    for linha in texto.splitlines():
        achado = MARCADOR_ANCORA.match(linha)
        saida.append(f"@@ANCORA:{achado.group(1)}@@\n" if achado else linha)
    return "\n".join(saida)


def dimensoes_png(caminho: Path) -> tuple[int, int]:
    with caminho.open("rb") as arquivo:
        cabecalho = arquivo.read(24)
    return struct.unpack(">II", cabecalho[16:24])


def texto_inline(token: Token) -> str:
    return "".join(f.content for f in token.children or [] if f.type in ("text", "code_inline"))


def escapar_template(valor: str) -> str:
    return valor.replace("{{", "&#123;&#123;").replace("{%", "&#123;%").replace("{#", "&#123;#")


class Conversor:
    def __init__(self, ancoras: dict[str, str], erros: list[str]):
        self.ancoras = ancoras
        self.erros = erros
        self.md = MarkdownIt("commonmark", {"html": True}).enable("table")
        self.md.renderer.rules["table_open"] = lambda t, i, o, e: '<div class="manual-tabela"><table>'
        self.md.renderer.rules["table_close"] = lambda t, i, o, e: "</table></div>"

    def converter(self, slug: str, texto: str):
        tokens = self.md.parse(preparar_ancoras(texto))
        tokens = self._ancoras_e_figuras(slug, tokens)
        sumario, secoes, usados = [], [], set()
        secao = None
        for i, token in enumerate(tokens):
            if token.type == "heading_open":
                inline = tokens[i + 1]
                titulo = texto_inline(inline)
                identificador = token.attrGet("id") or slug_titulo(titulo)
                base, n = identificador, 2
                while identificador in usados:
                    identificador, n = f"{base}-{n}", n + 1
                usados.add(identificador)
                token.attrSet("id", identificador)
                nivel = int(token.tag[1])
                if nivel in (2, 3):
                    sumario.append({"id": identificador, "nivel": nivel, "texto": titulo})
                secao = {"i": identificador, "h": titulo, "x": []}
                secoes.append(secao)
            elif token.type == "inline" and secao is not None:
                secao["x"].append(texto_inline(token))
            elif token.type == "blockquote_open":
                self._aviso(tokens, i)
            if token.type == "inline":
                self._links(slug, token)
        html = self.md.renderer.render(tokens, self.md.options, {})
        busca = [
            {"c": slug, "i": s["i"], "h": s["h"], "x": " ".join(s["x"])[:LIMITE_TEXTO_BUSCA]}
            for s in secoes
        ]
        return html, sumario, busca

    def _ancoras_e_figuras(self, slug: str, tokens: list[Token]) -> list[Token]:
        saida, pendentes, i = [], [], 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "paragraph_open":
                inline = tokens[i + 1]
                marcador = MARCADOR_TEXTO.match(inline.content.strip())
                if marcador:
                    pendentes.append(marcador.group(1))
                    i += 3
                    continue
                filhos = [f for f in (inline.children or []) if f.type != "softbreak"]
                if len(filhos) == 1 and filhos[0].type == "image":
                    figura = Token("html_block", "", 0)
                    figura.content = self._figura(filhos[0]) + "\n"
                    figura.block = True
                    saida.append(figura)
                    i += 3
                    continue
            if pendentes and token.nesting == 1 and token.level == 0 and not token.attrGet("id"):
                token.attrSet("id", pendentes.pop(0))
                for extra in pendentes:
                    self.erros.append(f"{slug}: âncora '{extra}' sem bloco próprio para receber o id")
                pendentes = []
            saida.append(token)
            i += 1
        if pendentes:
            self.erros.append(f"{slug}: âncora(s) {pendentes} sem bloco depois")
        return saida

    def _figura(self, imagem: Token) -> str:
        origem = imagem.attrGet("src")
        legenda = imagem.content
        arquivo = IMAGENS / Path(origem).name
        if not origem.startswith("assets/") or not arquivo.exists():
            self.erros.append(f"imagem inexistente: {origem}")
            return ""
        largura, altura = dimensoes_png(arquivo)
        destino = f"{{% url 'manual:imagem' '{arquivo.name}' %}}"
        legenda_html = self.md.renderInline(legenda)
        return (
            f'<figure class="manual-figura">'
            f'<a href="{destino}" target="_blank" rel="noopener" data-ampliar>'
            f'<img src="{destino}" alt="" loading="lazy" width="{largura}" height="{altura}">'
            f"</a><figcaption>{escapar_template(legenda_html)}</figcaption></figure>"
        )

    def _aviso(self, tokens: list[Token], i: int) -> None:
        # primeiro texto do aviso: um paragraph_open, o inline e então o texto
        inline = next((t for t in tokens[i + 1:i + 4] if t.type == "inline"), None)
        classe = "manual-aviso manual-aviso--neutro"
        if inline and inline.children:
            primeiro = inline.children[0]
            if primeiro.type == "text" and primeiro.content:
                simbolo = primeiro.content[0]
                if simbolo in AVISOS:
                    classe = f"manual-aviso manual-aviso--{AVISOS[simbolo]}"
                    primeiro.content = primeiro.content[1:].lstrip("️ \t")
        tokens[i].attrJoin("class", classe)

    def _links(self, slug: str, inline: Token) -> None:
        aberto = None
        for filho in inline.children or []:
            if filho.type == "link_open":
                aberto = filho
                href = filho.attrGet("href") or ""
                novo = self._destino(slug, href)
                if novo is None:
                    filho.type, filho.content, filho.attrs = "html_inline", "", {}
                    filho.nesting = 0
                    filho.meta = {"descartado": True}
                else:
                    filho.attrSet("href", novo)
                    if novo.startswith("http"):
                        filho.attrSet("target", "_blank")
                        filho.attrSet("rel", "noopener")
            elif filho.type == "link_close" and aberto is not None:
                if aberto.meta.get("descartado"):
                    filho.type, filho.content, filho.nesting = "html_inline", "", 0
                aberto = None

    def _destino(self, slug: str, href: str) -> str | None:
        if href.startswith("#"):
            alvo = href[1:]
            dono = self.ancoras.get(alvo)
            if dono is None:
                self.erros.append(f"{slug}: link para âncora inexistente '#{alvo}'")
                return href
            if dono == slug:
                return href
            if dono in DINAMICOS:
                return f"{{% url 'manual:capitulo' '{dono}' %}}"
            return f"{{% url 'manual:capitulo' '{dono}' %}}#{alvo}"
        if href.startswith(("http://", "https://")):
            return href
        if href.endswith(".md"):
            self.erros.append(f"{slug}: link para documento interno '{href}' foi removido; reescreva o trecho")
            return None
        if href.startswith("assets/"):
            return f"{{% url 'manual:imagem' '{href[len('assets/'):]}' %}}"
        self.erros.append(f"{slug}: link não tratado '{href}'")
        return href


def coletar_ancoras(secoes_por_slug: dict[str, str]) -> dict[str, str]:
    ancoras: dict[str, str] = {slug: slug for slug in DINAMICOS}
    for slug, texto in secoes_por_slug.items():
        for linha in texto.splitlines():
            achado = MARCADOR_ANCORA.match(linha)
            if achado:
                ancoras[achado.group(1)] = slug
            elif linha.startswith("#"):
                ancoras.setdefault(slug_titulo(linha.lstrip("# ")), slug)
    return ancoras


def gerar() -> dict[Path, str]:
    secoes, meta = dividir_secoes(ORIGEM.read_text(encoding="utf-8"))
    paginas: dict[str, str] = {}
    for capitulo in CAPITULOS:
        if not capitulo.secoes:
            continue
        faltando = [s for s in capitulo.secoes if s not in secoes]
        if faltando:
            raise SystemExit(f"seção não encontrada no manual: {faltando}")
        paginas[capitulo.slug] = "\n\n".join(secoes[s] for s in capitulo.secoes)
    sobra = set(secoes) - SECOES_DESCARTADAS - {s for c in CAPITULOS for s in c.secoes}
    if sobra:
        raise SystemExit(f"seções do manual sem capítulo no registro: {sorted(sobra)}")

    erros: list[str] = []
    conversor = Conversor(coletar_ancoras(paginas), erros)
    arquivos: dict[Path, str] = {}
    metadados = {"versao": meta.get("Versão", ""), "atualizado": meta.get("Última atualização", ""), "paginas": {}}
    busca: list[dict] = []
    for slug, texto in paginas.items():
        html, sumario, entradas = conversor.converter(slug, texto)
        corpo = "<div class=\"manual-prosa\">\n" + html + "</div>\n"
        arquivos[DESTINO_CAPITULOS / f"{slug}.html"] = corpo
        metadados["paginas"][slug] = {"sumario": sumario}
        busca.extend(entradas)

    residuos = [s for s in AVISOS if any(s in c for c in arquivos.values())]
    if residuos:
        erros.append(f"emoji de aviso fora de citação: {residuos}")
    if erros:
        raise SystemExit("\n".join(["Problemas no manual:", *sorted(set(erros))]))

    arquivos[DESTINO_METADADOS] = json.dumps(metadados, ensure_ascii=False, indent=1) + "\n"
    arquivos[DESTINO_BUSCA] = json.dumps(busca, ensure_ascii=False, separators=(",", ":")) + "\n"
    return arquivos


def main() -> int:
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--check", action="store_true")
    argumentos = analisador.parse_args()
    arquivos = gerar()
    if argumentos.check:
        velhos = [str(c.relative_to(RAIZ)) for c, t in arquivos.items()
                  if not c.exists() or c.read_text(encoding="utf-8") != t]
        if velhos:
            print("Desatualizados (rode scripts/gerar_manual_html.py):", *velhos, sep="\n  ")
            return 1
        print("Manual HTML em dia.")
        return 0
    for caminho, texto in arquivos.items():
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8", newline="\n")
    print(f"{len(arquivos)} arquivos gerados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
