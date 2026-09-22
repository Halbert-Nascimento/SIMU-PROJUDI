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


def feedback(nota=8.0):
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
        "form": Obj(estrelas=campo_form(4, ["Escolha de 1 a 5 estrelas."] if com_erros else []),
                    comentario=campo_form("", ["Este campo é obrigatório."] if com_erros else [])),
        "feedback_existente": feedback(),
        "mov_origem": movimentacao(com_documentos=False),
        "feedback_origem": feedback(None),
        "historico": hist,
        "media_notas": 4.1 if com_historico else None,
        "breadcrumbs": [{"label": "Área do Servidor", "url": "/"},
                        {"label": f"Processo {NUMERO}", "url": "/p/"},
                        {"label": "Avaliar Movimentação", "url": None}],
    }


def avaliacao_json(estrelas, faixa):
    # o mesmo template que a view usa para o desenho das estrelas
    from avaliacoes.estrelas import contexto_estrelas
    return {"id": 1, "data": "26/08/2026", "mov": "Juntada",
            "mov_texto": "…", "proc": NUMERO, "prof": "Ana Ribeiro",
            "prof_iniciais": "AR", "estrelas": estrelas, "faixa": faixa,
            "estrelas_html": render_to_string(
                "avaliacoes/components/_estrelas.html",
                contexto_estrelas(estrelas, herda_cor=True)),
            "comentario": "Boa peça.", "documentos": []}


def ctx_minhas_notas(vazio=False):
    fbs = [] if vazio else [feedback(10.0), feedback(None), feedback(6.0)]
    return {
        "user": ALUNO, "request": Obj(user=ALUNO),
        "feedbacks": fbs,
        "feedbacks_json": [avaliacao_json(5, "ok"), avaliacao_json(None, "gray"),
                           avaliacao_json(3, "warn")],
        "total_movimentacoes": 0 if vazio else 7,
        "total_avaliadas": 0 if vazio else 3,
        "media_geral": None if vazio else 3.9,
        "media_percentual": 0 if vazio else 78,
        "melhor_avaliacao": None if vazio else 5,
        "ultima_avaliacao": None if vazio else feedback(),
        "breadcrumbs": [{"label": "Área do Servidor", "url": "/"},
                        {"label": "Minhas Notas", "url": None}],
    }


class _Ciclo:
    pk = 7

    def __str__(self):
        return "2026.2 — Prática Jurídica"


def _filtro_ciclo(com_erro=False):
    ciclo = Obj(id_for_label="id_ciclo", value=lambda: "7",
                errors=["Ciclo inválido para o seu perfil."] if com_erro else [])
    return Obj(ciclo=ciclo, fields=Obj(ciclo=Obj(queryset=[_Ciclo()])))


def ctx_relatorio_notas(variante="com_notas"):
    vazio = variante == "vazio"
    linhas = [] if vazio else [
        {"aluno": ALUNO, "ciclo": Obj(nome_edicao="2026.2 — Prática Jurídica"),
         "total_movimentacoes": 7, "total_avaliadas": 3, "media": 3.9, "faixa": "warn"},
        {"aluno": ALUNO, "ciclo": Obj(nome_edicao="2026.2 — Prática Jurídica"),
         "total_movimentacoes": 0, "total_avaliadas": 0, "media": None, "faixa": "gray"},
    ]
    return {
        "user": PROFESSOR, "request": Obj(user=PROFESSOR, path="/avaliacoes/relatorio-notas/"),
        "form_filtro": _filtro_ciclo(com_erro=variante == "filtro_invalido"),
        "linhas": linhas, "total_alunos": 0 if vazio else 1,
        "total_avaliadas": 0 if vazio else 3, "total_movimentacoes": 0 if vazio else 7,
        "media_geral": None if vazio else 3.9,
        "breadcrumbs": [{"label": "Painel Administrativo", "url": "/"},
                        {"label": "Relatório de Notas", "url": None}],
    }


def ctx_avaliacoes_pendentes(vazio=False):
    pendentes = [] if vazio else [
        Obj(pk=1, tipo_movimento=Obj(nome_movimentacao="Juntada de contestação"),
            autor=ALUNO, data_movimento=QUANDO,
            processo=Obj(numero=NUMERO, ciclo=Obj(nome_edicao="2026.2 — Prática Jurídica"))),
    ]
    return {
        "user": PROFESSOR, "request": Obj(user=PROFESSOR, path="/avaliacoes/pendentes/"),
        "form_filtro": _filtro_ciclo(),
        "pendentes": pendentes, "total_alunos_aguardando": len(pendentes),
        "mais_antiga": None if vazio else QUANDO,
        "breadcrumbs": [{"label": "Painel Administrativo", "url": "/"},
                        {"label": "Avaliações Pendentes", "url": None}],
    }


def ctx_boas_vindas(ja_participou=False):
    return {
        "user": ALUNO, "request": Obj(user=ALUNO),
        "ja_participou": ja_participou,
    }


def ctx_visualizar(sem_movimentacao=False, com_arquivo=True, pode_alterar=True):
    doc = Obj(titulo_arquivo="contestacao.pdf", data_upload=QUANDO,
              caminho_arquivo=Obj(url="/media/contestacao.pdf", name="contestacao.pdf"))
    movs = [] if sem_movimentacao else [
        Obj(id=i, autor_id=9, nome="Juntada de contestação",
            descricao="Documento juntado aos autos.", data=QUANDO,
            autor_nome="Ana Ribeiro Alves",
            documentos=[doc] if (com_arquivo and i % 2 == 0) else [],
            tem_feedback=i % 3 == 0,
            efeitos_colaterais=["abre_prazo", "notifica"] if i == 5 else [])
        for i in range(1, 13)
    ]
    parte = Obj(nome="Maria Souza Lima", documento="123.456.789-00",
                tipo_parte=Obj(nome="Autor"))
    return {
        "user": PROFESSOR, "request": Obj(user=PROFESSOR),
        "processo": Obj(
            numero=NUMERO, classe=Obj(nome="Procedimento Comum Cível"),
            tipo_processo=Obj(nome="Cível"), comarca=Obj(nome="Goiânia"),
            vara=Obj(nome="1ª Vara Cível", comarca=Obj(nome="Goiânia"), comarca_id=1),
            valor_causa="15000.00",
            data_distribuicao=QUANDO, segredo_justica=False,
            status_atual="EM_ANDAMENTO", ciclo=Obj(nome_edicao="2026.2"),
            vara_id=10, tipo_processo_id=1, classe_id=5,
        ),
        "polos_ativo": [parte], "polos_passivo": [parte], "polos_terceiro": [],
        "grupo_serventia": Obj(nome="Serventia 1"),
        "grupos_vinculados": [Obj(nome="Grupo 1",
                                  cargo_simulacao=Obj(nome="Advogado do Polo Ativo"))],
        "movimentacoes": movs,
        "pode_avaliar": True,
        "pode_editar_processo": pode_alterar,
        "comarcas": [Obj(pk=1, nome="Goiânia"), Obj(pk=2, nome="Anápolis")],
        "varas_da_comarca": [Obj(pk=10, nome="1ª Vara Cível"), Obj(pk=11, nome="2ª Vara Cível")],
        "tipos_processo": [Obj(pk=1, nome="Cível"), Obj(pk=2, nome="Criminal")],
        "classes_processuais": [Obj(pk=5, nome="Procedimento Comum Cível")],
        "partes_json": [
            {"id": 1, "nome_razao": "Maria Souza Lima", "cpf_cnpj": "123.456.789-00",
             "tipo_pessoa": "Física", "polo": "Ativo"},
            {"id": 2, "nome_razao": "Construtora Alfa Ltda.", "cpf_cnpj": "12.345.678/0001-90",
             "tipo_pessoa": "Jurídica", "polo": "Passivo"},
        ],
        "breadcrumbs": [{"label": "Área do Servidor", "url": "/"},
                        {"label": f"Processo {NUMERO}", "url": None}],
    }


def ctx_documento_legal(logado=False):
    usr = ALUNO if logado else Obj(is_authenticated=False)
    return {
        "user": usr, "request": Obj(user=usr),
        "voltar_url": "base:home" if logado else "acesso:cadastro",
        "nome_instituicao": "Faculdade IESGO",
        "email_contato_dpo": "contato@simu-projudi.local",
        "foro_comarca": "Goiânia/GO",
        "versao_termos_atual": "1.0",
        "data_vigencia_termos": "2026-09-22",
    }


def ctx_aceite_termos(com_erro=False):
    msg = (
        "É necessário aceitar os Termos de Uso e a Política de Privacidade "
        "para continuar."
    )
    erros = [msg] if com_erro else []
    return {
        "user": ALUNO, "request": Obj(user=ALUNO),
        "form": Obj(aceite_termos=campo_form(None, erros)),
        "next": "/processos/area-servidor/",
    }


def ctx_login(com_erros=False, expirada=False):
    anonimo = Obj(is_authenticated=False)
    erros = ["Por favor, entre com um Usuário e senha corretos."] if com_erros else []
    return {
        "user": anonimo,
        "request": Obj(user=anonimo, path="/",
                       GET={"exp": "1"} if expirada else {}),
        "form": Obj(
            username=campo_form("maria.souza" if com_erros else None),
            password=campo_form(),
            non_field_errors=erros,
        ),
    }


def grupo_fake(nome, pk=1):
    return Obj(pk=pk, nome=nome)


def estado_posicao(chave, rotulo, ocupante=None, opcoes=(), conflito=(), indisponivel=False):
    vinculados = list(conflito) or ([ocupante] if ocupante else [])
    return Obj(
        posicao=Obj(chave=chave, rotulo=rotulo),
        grupo=None if conflito else ocupante,
        grupos_vinculados=vinculados,
        opcoes=list(opcoes),
        em_conflito=bool(conflito),
        indisponivel=indisponivel,
        pendente=not vinculados,
        impressao=",".join(str(g.pk) for g in vinculados),
    )


def processo_fake(status="Autuado"):
    return Obj(
        numero=NUMERO,
        vara=Obj(nome="1ª Vara Cível", comarca=Obj(nome="Goiânia")),
        classe=Obj(nome="Procedimento Comum Cível"),
        status_atual=Obj(nome_status=status),
    )


def ctx_atribuir_grupos(passo=1, variante="ocupadas"):
    alfa, beta = grupo_fake("Grupo Alfa", 1), grupo_fake("Grupo Beta", 2)
    app1, mp1, mp2 = grupo_fake("Grupo APP", 3), grupo_fake("Grupo MP 1", 4), grupo_fake("Grupo MP 2", 5)
    jz1 = grupo_fake("Grupo JZ 1", 6)

    if variante == "pendentes":
        estados = [
            estado_posicao("polo_ativo", "Polo ativo", opcoes=[alfa, beta, mp1]),
            estado_posicao("polo_passivo", "Polo passivo", opcoes=[app1]),
            estado_posicao("ministerio_publico", "Ministério Público (interveniente)", opcoes=[mp1]),
            estado_posicao("juiz", "Juiz", indisponivel=True),
        ]
    elif variante == "conflito":
        estados = [
            estado_posicao("polo_ativo", "Polo ativo", ocupante=alfa, opcoes=[beta]),
            estado_posicao("polo_passivo", "Polo passivo", conflito=[app1, grupo_fake("Grupo APP fora", 7)]),
            estado_posicao("ministerio_publico", "Ministério Público (interveniente)", opcoes=[mp1, mp2]),
            estado_posicao("juiz", "Juiz", ocupante=jz1),
        ]
    else:
        estados = [
            estado_posicao("polo_ativo", "Polo ativo", ocupante=alfa, opcoes=[beta, mp1]),
            estado_posicao("polo_passivo", "Polo passivo", ocupante=app1, opcoes=[]),
            estado_posicao("ministerio_publico", "Ministério Público (interveniente)", ocupante=mp1, opcoes=[mp2]),
            estado_posicao("juiz", "Juiz", ocupante=jz1),
        ]

    contexto = {
        "user": ALUNO, "request": Obj(user=ALUNO),
        "processo": processo_fake("Protocolado" if variante == "pendentes" else "Autuado"),
        "estados": estados,
        "proximo": "/processos/area-servidor/",
        "polos_ativo": [Obj(parte=Obj(nome_razao="João da Silva"))],
        "polos_passivo": [Obj(parte=Obj(nome_razao="Empresa Ré Ltda."))],
        "passo": passo,
        "breadcrumbs": [{"label": "Área do Servidor", "url": "/"},
                        {"label": f"Processo {NUMERO}", "url": "/p/"},
                        {"label": "Atribuir Grupos", "url": None}],
    }
    if passo == 2:
        posicao_ativo = Obj(chave="polo_ativo", rotulo="Polo ativo")
        posicao_mp = Obj(chave="ministerio_publico", rotulo="Ministério Público (interveniente)")
        contexto.update({
            "plano": Obj(
                alteracoes=[
                    Obj(natureza="substituicao", posicao=posicao_ativo,
                        grupo_anterior=alfa, grupo_novo=beta, posicao_origem=None),
                    Obj(natureza="atribuicao", posicao=Obj(chave="polo_passivo", rotulo="Polo passivo"),
                        grupo_anterior=None, grupo_novo=app1, posicao_origem=None),
                    Obj(natureza="mudanca_de_posicao", posicao=posicao_ativo,
                        grupo_anterior=None, grupo_novo=mp1, posicao_origem=posicao_mp),
                    Obj(natureza="remocao", posicao=Obj(chave="juiz", rotulo="Juiz"),
                        grupo_anterior=jz1, grupo_novo=None, posicao_origem=None),
                ],
                donos_de_polo={"Ativo": beta, "Passivo": app1},
                vinculos_a_remover=[alfa, jz1],
            ),
            "descricao_evento": 'Polo ativo: "Grupo Alfa" substituído por "Grupo Beta". '
                                'Juiz: "Grupo JZ 1" removido.',
            "nome_evento": "Redistribuição",
            "escolhas": {"posicao_polo_ativo": "2", "atual_polo_ativo": "1"},
        })
    return contexto


CASOS = [
    ("acesso/termos_de_uso.html", "visitante anônimo", ctx_documento_legal()),
    ("acesso/termos_de_uso.html", "usuário logado", ctx_documento_legal(logado=True)),
    ("acesso/politica_privacidade.html", "visitante anônimo", ctx_documento_legal()),
    ("acesso/aceite_termos_pendente.html", "formulário limpo", ctx_aceite_termos()),
    ("acesso/aceite_termos_pendente.html", "form com erro",
     ctx_aceite_termos(com_erro=True)),
    ("acesso/login.html", "form limpo", ctx_login()),
    ("acesso/login.html", "credenciais inválidas", ctx_login(com_erros=True)),
    ("acesso/login.html", "sessão expirada", ctx_login(expirada=True)),
    ("processos/visualizar_processo.html", "12 movimentações", ctx_visualizar()),
    ("processos/visualizar_processo.html", "sem movimentação", ctx_visualizar(sem_movimentacao=True)),
    ("processos/visualizar_processo.html", "sem arquivo anexo", ctx_visualizar(com_arquivo=False)),
    ("processos/visualizar_processo.html", "sem permissão de editar", ctx_visualizar(pode_alterar=False)),
    ("avaliacoes/avaliar.html", "com histórico", ctx_avaliar()),
    ("avaliacoes/avaliar.html", "form com erros", ctx_avaliar(com_erros=True)),
    ("avaliacoes/avaliar.html", "sem histórico", ctx_avaliar(com_historico=False)),
    ("avaliacoes/minhas_notas.html", "com avaliações", ctx_minhas_notas()),
    ("avaliacoes/minhas_notas.html", "sem avaliação", ctx_minhas_notas(vazio=True)),
    ("avaliacoes/relatorio_notas.html", "com notas", ctx_relatorio_notas()),
    ("avaliacoes/relatorio_notas.html", "sem aluno", ctx_relatorio_notas("vazio")),
    ("avaliacoes/relatorio_notas.html", "filtro inválido", ctx_relatorio_notas("filtro_invalido")),
    ("avaliacoes/avaliacoes_pendentes.html", "com pendências", ctx_avaliacoes_pendentes()),
    ("avaliacoes/avaliacoes_pendentes.html", "sem pendência", ctx_avaliacoes_pendentes(vazio=True)),
    ("ciclos/boas_vindas.html", "primeiro acesso", ctx_boas_vindas()),
    ("ciclos/boas_vindas.html", "ciclo anterior encerrado", ctx_boas_vindas(ja_participou=True)),
    ("processos/atribuir_grupos.html", "posições ocupadas", ctx_atribuir_grupos()),
    ("processos/atribuir_grupos.html", "pendentes e papel indisponível",
     ctx_atribuir_grupos(variante="pendentes")),
    ("processos/atribuir_grupos.html", "posição em conflito",
     ctx_atribuir_grupos(variante="conflito")),
    ("processos/atribuir_grupos.html", "resumo com as quatro naturezas",
     ctx_atribuir_grupos(passo=2)),
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
