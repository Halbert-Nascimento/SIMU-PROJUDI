#!/usr/bin/env python
"""
Renderiza de fato as telas do lote, com contexto dublado e sem banco.

    python scripts/render_smoke.py

`verificar.py check` apenas COMPILA: ele nao executa {% card %}, {% campo %},
{% modal %} nem os {% include %} de componente, entao um erro dentro do
componente — argumento que nao existe, filtro encadeado errado — so aparece
aqui. Cada tela roda em mais de uma variante: lista com dados e vazia,
formulario limpo e com erros.

Falha tambem se sobrar `{{` ou `{%` no HTML final: e o sinal de tag nao fechada
ou de variavel que o template imprimiu como texto.

Ao converter uma tela nova, acrescente o caso em CASOS.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as Obj

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django                                             # noqa: E402

django.setup()

from django.template.loader import render_to_string       # noqa: E402


# ── dublês ──────────────────────────────────────────────────────────────────
def usuario(perfil="ALUNO", nome="Maria Souza Lima"):
    primeiro, _, ultimo = nome.partition(" ")
    return Obj(
        is_authenticated=True, username="maria.souza", email="maria@iesgo.edu.br",
        first_name=primeiro, last_name=ultimo or "Lima",
        get_full_name=lambda: nome, tipo_perfil_global=perfil,
    )


ALUNO = usuario()
PROFESSOR = usuario("PROFESSOR", "Ana Ribeiro Alves")
NUMERO = "5012788-42.2026.8.09.0079"
QUANDO = datetime(2026, 8, 26, 14, 30, 12)


def movimentacao(com_documentos=True):
    docs = [Obj(titulo_arquivo="peticao.pdf", data_upload=QUANDO,
                caminho_arquivo=Obj(url="/media/peticao.pdf"))] if com_documentos else []
    return Obj(
        tipo_movimento=Obj(nome_movimentacao="Juntada de contestação"),
        data_movimento=QUANDO,
        descricao_evento="Texto da movimentação registrada nos autos.",
        documentos=Obj(all=lambda: docs),
        processo=Obj(numero=NUMERO),
    )


def campo_form(valor=None, erros=()):
    return Obj(value=lambda: valor, errors=list(erros), id_for_label="id_campo")


def feedback(nota=8.5):
    return Obj(nota=nota, data_feedback=QUANDO, professor=PROFESSOR,
               comentario="Boa fundamentação.", movimentacao=movimentacao())


def ctx_avaliar(com_erros=False, com_historico=True):
    hist = [feedback(9.0), feedback(None)] if com_historico else []
    return {
        "user": PROFESSOR, "request": Obj(user=PROFESSOR),
        "movimentacao": movimentacao(),
        "processo": Obj(numero=NUMERO, classe=Obj(nome="Procedimento Comum Cível")),
        "ciclo": "2026.2 — Prática Jurídica", "autor": ALUNO,
        "grupo_autor": Obj(nome="Grupo 1", cargo_simulacao=Obj(nome="Advogado do Polo Ativo")),
        "form": Obj(nota=campo_form(8.5, ["Informe um valor entre 0 e 10."] if com_erros else []),
                    comentario=campo_form("", ["Este campo é obrigatório."] if com_erros else [])),
        "feedback_existente": feedback(),
        "mov_origem": movimentacao(com_documentos=False),
        "feedback_origem": feedback(None),
        "historico": hist,
        "media_notas": 8.25 if com_historico else None,
        "breadcrumbs": [{"label": "Área do Servidor", "url": "/"},
                        {"label": f"Processo {NUMERO}", "url": "/p/"},
                        {"label": "Avaliar Movimentação", "url": None}],
    }


def ctx_minhas_notas(vazio=False):
    fbs = [] if vazio else [feedback(9.2), feedback(None), feedback(5.5)]
    return {
        "user": ALUNO, "request": Obj(user=ALUNO),
        "feedbacks": fbs,
        "feedbacks_json": [{"id": 1, "data": "26/08/2026", "mov": "Juntada",
                            "mov_texto": "…", "proc": NUMERO, "prof": "Ana Ribeiro",
                            "prof_iniciais": "AR", "nota": 9.2,
                            "comentario": "Boa peça.", "documentos": []}],
        "total_movimentacoes": 0 if vazio else 7,
        "total_avaliadas": 0 if vazio else 3,
        "media_geral": None if vazio else 7.9,
        "melhor_nota": None if vazio else 9.2,
        "ultima_avaliacao": None if vazio else feedback(),
        "breadcrumbs": [{"label": "Área do Servidor", "url": "/"},
                        {"label": "Minhas Notas", "url": None}],
    }


def ctx_redirecionamento(vazio=False):
    rotas = [] if vazio else [
        Obj(route="area-servidor/", name="processos:pagina_aluno", clickable=True),
        Obj(route="<str:numero>/", name="processos:visualizar_processo", clickable=False),
    ]
    return {"user": ALUNO, "request": Obj(user=ALUNO), "all_routes": rotas}


CASOS = [
    ("avaliacoes/avaliar.html", "com histórico", ctx_avaliar()),
    ("avaliacoes/avaliar.html", "form com erros", ctx_avaliar(com_erros=True)),
    ("avaliacoes/avaliar.html", "sem histórico", ctx_avaliar(com_historico=False)),
    ("avaliacoes/minhas_notas.html", "com avaliações", ctx_minhas_notas()),
    ("avaliacoes/minhas_notas.html", "sem avaliação", ctx_minhas_notas(vazio=True)),
    ("base/redirecionamento_teste_sucesso.html", "com rotas", ctx_redirecionamento()),
    ("base/redirecionamento_teste_sucesso.html", "sem rota", ctx_redirecionamento(vazio=True)),
]


def main() -> int:
    falhas = 0
    for template, variante, contexto in CASOS:
        rotulo = f"{template} ({variante})"
        try:
            html = render_to_string(template, contexto)
        except Exception as exc:                          # noqa: BLE001
            print(f"[FALHA] {rotulo}: {type(exc).__name__}: {exc}")
            falhas += 1
            continue
        # tag nao fechada ou variavel impressa como texto
        sobra = [m for m in ("{{", "{%") if m in html]
        if sobra:
            print(f"[FALHA] {rotulo}: sobrou {sobra} no HTML final")
            falhas += 1
            continue
        print(f"[ ok  ] {rotulo} — {len(html)} bytes")
    print(f"\n{falhas} falha(s)" if falhas else "\ntudo renderizou")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
