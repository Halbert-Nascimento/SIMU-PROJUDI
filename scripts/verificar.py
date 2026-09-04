#!/usr/bin/env python
"""
Verificacao estatica da troca de pele (Guia de Design IESGO).

    python scripts/verificar.py snapshot   # grava o estado atual das telas
    python scripts/verificar.py check      # checagens estaticas
    python scripts/verificar.py diff       # compara com o snapshot
    python scripts/verificar.py all        # check + diff

O invariante forte de uma troca de pele: o texto visivel e o conjunto de `id`
nao podem mudar — so atributos. `snapshot` grava os dois antes da conversao e
`diff` acusa qualquer perda depois dela.

Cada checagem nasceu de um defeito que passou batido:

  compilacao       template que nao carrega
  aninhamento      </tag> orfa ou cruzada
  classes orfas    classe que nao resolve para nada (o caso do max-w-container)
  escala de fonte  text-2xl e classe VALIDA: resolve, pinta, e nao esta no guia
  raio e sombra    o config zera `rounded*`/`shadow*` de CLASSE; um
                   `border-radius: 3px` dentro de <style>, de um .css ou de um
                   atributo style="" passa por fora e continua pintando
"""
from __future__ import annotations

import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APPS = ["acesso", "avaliacoes", "base", "ciclos", "processos", "usuarios"]
# peca processual, nao interface: Times 12pt e o formato correto do documento
FORA_DE_ESCOPO = ("templates/static/modelos/",)
SNAPSHOT = RAIZ / ".verificacao-snapshot.json"
CONFIG = RAIZ / "templates/static/js/tailwind.config.global.js"

# nomes de fontSize que o Tailwind resolve sozinho — validos, e fora do guia
ESCALA_TAILWIND = {"xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl",
                   "5xl", "6xl", "7xl", "8xl", "9xl"}

# raios que o guia admite: 0 (conteiner e botao), 2px (campo), 50% (avatar)
RAIOS_OK = {"0", "0px", "2px", "50%", "9999px", "inherit", "initial", "unset"}
# as duas unicas sombras do guia: modal e halo de validacao
SOMBRAS_OK = ("rgba(10,8,61,.45)", "rgba(10, 8, 61, .45)",
              "rgba(192,57,43,.12)", "rgba(192, 57, 43, .12)",
              "none", "inherit", "initial", "unset")

TAGS_VAZIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
               "link", "meta", "param", "source", "track", "wbr"}

# argumentos de tag Django que carregam texto visivel ou id — sem le-los, toda
# adocao de componente aparece como perda de conteudo
ARGS_TEXTO = ("titulo", "label", "ajuda", "voltar_label", "mensagem", "apoio",
              "rotulo", "meta")
ARGS_ID = ("id", "fechar_id", "container_id", "info_id", "paginas_id",
           "btn_prefixo")

# classes que o Tailwind resolve sem passar pelo tema
CORES_UTILITARIAS = {
    "white", "black", "transparent", "current", "inherit", "auto", "center",
    "left", "right", "justify", "start", "end", "top", "bottom", "middle",
    "baseline", "wrap", "nowrap", "clip", "ellipsis", "balance", "pretty",
}

# CSS escrito dentro de <script> (o documento gerado por movimentar_processo)
# casa com o padrao de classe sem ser classe
PROPRIEDADES_CSS = {
    "text-align", "text-transform", "text-decoration", "text-shadow",
    "text-overflow", "text-indent", "border-color", "border-radius",
    "border-collapse", "border-spacing", "border-style", "border-width",
    "border-box", "bg-color", "z-index", "max-width",
}


def templates() -> list[Path]:
    achados: list[Path] = []
    for app in APPS:
        achados += sorted((RAIZ / app).rglob("*.html"))
    achados += sorted((RAIZ / "templates").rglob("*.html"))
    return [p for p in achados
            if ".venv" not in p.parts and not rel(p).startswith(FORA_DE_ESCOPO)]


def folhas_css() -> list[Path]:
    return sorted((RAIZ / "templates/static/css").rglob("*.css"))


def rel(p: Path) -> str:
    return str(p.relative_to(RAIZ)).replace("\\", "/")


# ── snapshot: texto visivel + conjunto de ids ───────────────────────────────
def _args_de_tags(fonte: str, nomes: tuple[str, ...]) -> list[str]:
    achados = []
    for nome in nomes:
        for m in re.finditer(nome + r"=([\"'])(.*?)\1", fonte):
            achados.append(m.group(2))
    return achados


def texto_visivel(fonte: str) -> list[str]:
    """Palavras que o usuario le, incluindo as que moram dentro de {% tag %}."""
    dos_args = _args_de_tags(fonte, ARGS_TEXTO)

    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fonte)
    s = re.sub(r"(?s)\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", " ", s)
    s = re.sub(r"(?s)\{#.*?#\}", " ", s)          # comentario Django de uma linha
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?s)\{%.*?%\}", " ", s)
    s = re.sub(r"(?s)\{\{.*?\}\}", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = " ".join([s] + dos_args)
    return [p for p in re.split(r"\s+", s.strip()) if p]


def ids_do_template(fonte: str) -> list[str]:
    sem_script = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fonte)
    do_html = re.findall(r"\bid=\"([^\"{}]+)\"", sem_script)
    return sorted(set(do_html) | set(_args_de_tags(fonte, ARGS_ID)))


def montar_snapshot() -> dict:
    estado = {}
    for p in templates():
        fonte = p.read_text(encoding="utf-8")
        estado[rel(p)] = {"texto": texto_visivel(fonte), "ids": ids_do_template(fonte)}
    return estado


def _sobras(a: list[str], b: list[str]) -> list[str]:
    """Itens de `a` que `b` nao cobre, contando repeticoes."""
    resto = list(b)
    fora = []
    for item in a:
        if item in resto:
            resto.remove(item)
        else:
            fora.append(item)
    return fora


def cmd_snapshot() -> int:
    estado = montar_snapshot()
    SNAPSHOT.write_text(json.dumps(estado, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print("snapshot de %d templates em %s" % (len(estado), SNAPSHOT.name))
    return 0


def cmd_diff() -> int:
    if not SNAPSHOT.exists():
        print("sem snapshot — rode `python scripts/verificar.py snapshot` antes")
        return 1
    antes = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    agora = montar_snapshot()
    perdas = 0

    for nome in sorted(set(antes) | set(agora)):
        a, b = antes.get(nome), agora.get(nome)
        if a is None:
            print("  [novo ] %s" % nome)
            continue
        if b is None:
            print("  [SUMIU] %s" % nome)
            perdas += 1
            continue

        perdido = _sobras(a["texto"], b["texto"])
        entrou = _sobras(b["texto"], a["texto"])
        if perdido:
            print("  [TEXTO] %s: sumiu %s" % (nome, perdido[:14]))
            perdas += 1
        if entrou:
            print("  [texto] %s: entrou %s" % (nome, entrou[:14]))

        ids_perdidos = sorted(set(a["ids"]) - set(b["ids"]))
        ids_novos = sorted(set(b["ids"]) - set(a["ids"]))
        if ids_perdidos:
            print("  [ID   ] %s: sumiu %s" % (nome, ids_perdidos))
            perdas += 1
        if ids_novos:
            print("  [id   ] %s: entrou %s" % (nome, ids_novos))

    print("diff: nada perdido" if not perdas else "diff: %d perda(s)" % perdas)
    return 1 if perdas else 0


# ── checagem: compilacao ────────────────────────────────────────────────────
def checar_compilacao() -> int:
    try:
        import django
    except ImportError:
        print("  django ausente — checagem pulada")
        return 0
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    sys.path.insert(0, str(RAIZ))
    try:
        django.setup()
    except Exception as exc:                                   # noqa: BLE001
        print("  django.setup() falhou (%s) — checagem pulada" % exc)
        return 0

    from django.template import TemplateSyntaxError
    from django.template.loader import get_template

    falhas = vistos = 0
    for p in templates():
        partes = p.relative_to(RAIZ).parts
        if "templates" not in partes:
            continue
        nome = "/".join(partes[partes.index("templates") + 1:])
        try:
            get_template(nome)
            vistos += 1
        except TemplateSyntaxError as exc:
            print("  [ERRO] %s: %s" % (rel(p), exc))
            falhas += 1
        except Exception:                                      # noqa: BLE001
            pass                                               # fora do loader
    print("  compilacao: %d templates, %d erro(s)" % (vistos, falhas))
    return falhas


# ── checagem: aninhamento ───────────────────────────────────────────────────
class _Aninhamento(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pilha: list[str] = []
        self.erros: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS_VAZIAS:
            self.pilha.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in TAGS_VAZIAS:
            return
        linha = self.getpos()[0]
        if tag in self.pilha:
            if self.pilha[-1] == tag:
                self.pilha.pop()
                return
            i = len(self.pilha) - 1 - self.pilha[::-1].index(tag)
            self.erros.append("linha %d: </%s> fecha por cima de <%s>"
                              % (linha, tag, self.pilha[i + 1]))
            del self.pilha[i:]
            return
        self.erros.append("linha %d: </%s> sem abertura" % (linha, tag))


def checar_aninhamento() -> int:
    falhas = 0
    for p in templates():
        fonte = p.read_text(encoding="utf-8")
        # o parser nao entende {% if %}: apaga as tags mantendo as linhas
        limpo = re.sub(r"(?s)\{%.*?%\}",
                       lambda m: "\n" * m.group().count("\n"), fonte)
        limpo = re.sub(r"(?s)\{\{.*?\}\}", " ", limpo)
        par = _Aninhamento()
        try:
            par.feed(limpo)
        except Exception as exc:                               # noqa: BLE001
            par.erros.append(str(exc))
        for e in par.erros:
            print("  [ERRO] %s %s" % (rel(p), e))
        falhas += len(par.erros)
    print("  aninhamento: %d erro(s)" % falhas)
    return falhas


# ── checagem: classes orfas ─────────────────────────────────────────────────
def tokens_do_config() -> dict[str, set[str]]:
    fonte = CONFIG.read_text(encoding="utf-8")

    def bloco(nome: str) -> str:
        m = re.search(nome + r":\s*\{", fonte)
        if not m:
            return ""
        i, prof = m.end() - 1, 0
        for j in range(i, len(fonte)):
            if fonte[j] == "{":
                prof += 1
            elif fonte[j] == "}":
                prof -= 1
                if prof == 0:
                    return fonte[i:j]
        return ""

    def chaves(texto: str) -> set[str]:
        return set(re.findall(r"['\"]?([\w-]+)['\"]?\s*:", texto))

    return {
        "cor": chaves(bloco("colors")),
        "fonte": chaves(bloco("fontSize")),
        "maxw": chaves(bloco("maxWidth")),
        "raio": chaves(bloco("borderRadius")),
        "sombra": chaves(bloco("boxShadow")),
        "z": chaves(bloco("zIndex")),
    }


def checar_classes_orfas(tokens: dict[str, set[str]]) -> int:
    padrao = re.compile(
        r"(?:hover:|focus:|active:|group-hover:|disabled:|last:|lg:|md:|sm:|xl:)*"
        r"\b(bg|text|border|max-w|rounded|shadow|z)-([a-z0-9][\w-]*)\b")
    falhas = 0
    for p in templates():
        fonte = p.read_text(encoding="utf-8")
        # CSS escrito a mao usa `text-align`, `border-color`, `z-index`: nomes de
        # propriedade, nao classe. O <script> FICA — classe em string de
        # JavaScript tambem e pele, e ja quebrou uma tela.
        fonte = re.sub(r"(?is)<style\b.*?</style>", " ", fonte)
        fonte = re.sub(r"(?is)\bstyle=\"[^\"]*\"", " ", fonte)
        for m in padrao.finditer(fonte):
            grupo, valor = m.group(1), m.group(2)
            if m.group(0).lstrip(":") in PROPRIEDADES_CSS:
                continue
            if grupo in ("bg", "text", "border"):
                # border-t-navy / border-l-atencao-txt: o lado nao e o valor;
                # border-b sozinho e a borda de 1px daquele lado
                if grupo == "border":
                    if re.fullmatch(r"[trblxyse]", valor):
                        continue
                    valor = re.sub(r"^(?:[trblxyse])-", "", valor)
                if valor in CORES_UTILITARIAS or valor in tokens["cor"]:
                    continue
                if grupo == "text" and (valor in tokens["fonte"]
                                        or valor in ESCALA_TAILWIND):
                    continue
                if grupo == "border" and re.fullmatch(
                        r"\d+|dashed|solid|none|collapse|separate", valor):
                    continue
                if grupo == "bg" and re.fullmatch(
                        r"opacity-\d+|cover|contain|no-repeat|clip|origin-\w+", valor):
                    continue
            elif grupo == "max-w":
                if valor in tokens["maxw"] or valor in (
                        ESCALA_TAILWIND | {"full", "none", "prose", "screen", "min",
                                           "max", "fit"}):
                    continue
            elif grupo == "rounded":
                # rounded-r-sm: o r/l e o LADO, nao o tamanho
                nucleo = re.sub(r"^(?:tl|tr|bl|br|[trblse])-", "", valor)
                if nucleo in tokens["raio"] or nucleo in ("full", "none"):
                    continue
            elif grupo == "shadow":
                if valor in tokens["sombra"]:
                    continue
            elif grupo == "z":
                if valor in tokens["z"] or valor.isdigit() or valor == "auto":
                    continue
            print("  [ORFA] %s: %s" % (rel(p), m.group(0)))
            falhas += 1
    print("  classes orfas: %d" % falhas)
    return falhas


# ── checagem: escala tipografica ────────────────────────────────────────────
def checar_escala_fonte() -> int:
    padrao = re.compile(r"\btext-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)\b")
    total = 0
    por_arquivo: dict[str, int] = {}
    for p in templates():
        n = len(padrao.findall(p.read_text(encoding="utf-8")))
        if n:
            por_arquivo[rel(p)] = n
            total += n
    for nome, n in sorted(por_arquivo.items(), key=lambda kv: -kv[1]):
        print("  [aviso] %s: %d fora da escala do guia" % (nome, n))
    print("  escala de fonte: %d aviso(s)" % total)
    return 0                                          # aviso, nao falha


# ── checagem: raio e sombra escritos a mao ──────────────────────────────────
def checar_raio_sombra() -> int:
    falhas = 0
    alvos: list[tuple[Path, str]] = [(p, p.read_text(encoding="utf-8"))
                                     for p in folhas_css()]
    for p in templates():
        fonte = p.read_text(encoding="utf-8")
        trechos = re.findall(r"(?is)<style\b[^>]*>(.*?)</style>", fonte)
        trechos += re.findall(r"(?is)\bstyle=\"([^\"]*)\"", fonte)
        if trechos:
            alvos.append((p, "\n".join(trechos)))

    for p, css in alvos:
        for m in re.finditer(r"border-radius\s*:\s*([^;}\n]+)", css):
            bruto = m.group(1).replace("!important", "").strip().rstrip(";")
            valores = bruto.split()
            if all(v in RAIOS_OK for v in valores):
                continue
            print("  [RAIO ] %s: border-radius: %s" % (rel(p), m.group(1).strip()))
            falhas += 1
        for m in re.finditer(r"box-shadow\s*:\s*([^;}\n]+)", css):
            valor = m.group(1).strip().rstrip(";")
            if any(f in valor for f in SOMBRAS_OK):
                continue
            print("  [SOMBR] %s: box-shadow: %s" % (rel(p), valor))
            falhas += 1
    print("  raio e sombra em CSS: %d" % falhas)
    return falhas


def cmd_check() -> int:
    tokens = tokens_do_config()
    total = 0
    print("compilacao")
    total += checar_compilacao()
    print("aninhamento")
    total += checar_aninhamento()
    print("classes orfas")
    total += checar_classes_orfas(tokens)
    print("escala de fonte")
    total += checar_escala_fonte()
    print("raio e sombra")
    total += checar_raio_sombra()
    print("\ncheck: %d problema(s)" % total)
    return 1 if total else 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "snapshot":
        return cmd_snapshot()
    if cmd == "check":
        return cmd_check()
    if cmd == "diff":
        return cmd_diff()
    if cmd == "all":
        return max(cmd_check(), cmd_diff())
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
