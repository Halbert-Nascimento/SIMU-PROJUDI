from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.text import slugify

from . import servicos
from .capitulos import CARGO_DO_CAPITULO, CAPITULOS, SLUG_LINHA_DO_PROCESSO
from .linha_processo import ORDEM_DOS_PAPEIS, atos_do_papel, montar_linha_do_processo


def _contexto_pagina(capitulo):
    anterior, seguinte = servicos.vizinhos(capitulo.slug)
    return {
        "capitulo": capitulo,
        "grupos": servicos.capitulos_por_grupo(),
        "sumario": servicos.sumario_da_pagina(capitulo.slug),
        "versao_manual": servicos.versao_do_manual(),
        "atualizado_em": servicos.atualizado_em(),
        "anterior": anterior,
        "seguinte": seguinte,
    }


def indice(request):
    return redirect("manual:capitulo", slug=CAPITULOS[0].slug)


def capitulo(request, slug):
    capitulo_atual = servicos.capitulo_ou_none(slug)
    if capitulo_atual is None:
        raise Http404("Capítulo inexistente.")
    contexto = _contexto_pagina(capitulo_atual)
    if capitulo_atual.slug == SLUG_LINHA_DO_PROCESSO:
        fases = montar_linha_do_processo()
        contexto.update(
            conteudo="manual/linha_do_processo_corpo.html",
            fases=fases,
            papeis_do_filtro=ORDEM_DOS_PAPEIS,
            sumario=[
                {"id": slugify(fase.nome), "nivel": 2, "texto": fase.nome}
                for fase in fases
            ],
        )
    else:
        contexto["conteudo"] = f"manual/capitulos/{capitulo_atual.slug}.html"
        cargo = CARGO_DO_CAPITULO.get(capitulo_atual.slug)
        if cargo:
            cod, nome = cargo
            fases = atos_do_papel(cod)
            contexto.update(
                atos_do_papel=fases,
                cargo_cod=cod,
                cargo_nome=nome,
                sumario=contexto["sumario"]
                + [{"id": "atos-do-papel", "nivel": 2, "texto": f"Atos de {nome}"}]
                + [{"id": f"atos-{slugify(f.nome)}", "nivel": 3, "texto": f.nome} for f in fases],
            )
    return render(request, "manual/capitulo.html", contexto)
