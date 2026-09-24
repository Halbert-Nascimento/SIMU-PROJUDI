from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from base.breadcrumbs import home_breadcrumb
from base.decorators import exige_permissao
from base.mensagens import propagar_erros_form

from .forms import FiltroCicloForm
from .estrelas import media_para_estrelas
from .permissions import pode_ver_avaliacoes_pendentes, pode_ver_relatorio_notas
from .services import (
    ciclos_do_avaliador,
    media_geral_das_notas,
    movimentacoes_pendentes_de_avaliacao,
    notas_por_aluno,
)


def _ciclos_filtrados(request, ciclos_disponiveis):
    """Aplica o filtro de ciclo da querystring; ciclo fora do recorte do perfil é ignorado."""
    form = FiltroCicloForm(request.GET or None, ciclos=ciclos_disponiveis)
    if form.is_valid() and form.cleaned_data["ciclo"]:
        return form, ciclos_disponiveis.filter(pk=form.cleaned_data["ciclo"].pk)
    if form.is_bound:
        propagar_erros_form(request, form)
    return form, ciclos_disponiveis


@login_required
@exige_permissao(pode_ver_relatorio_notas)
def relatorio_notas(request):
    ciclos_disponiveis = ciclos_do_avaliador(request.user).order_by(
        "-ano", "-semestre", "nome_edicao",
    )
    form_filtro, ciclos = _ciclos_filtrados(request, ciclos_disponiveis)

    linhas = notas_por_aluno(ciclos)

    return render(
        request,
        "avaliacoes/relatorio_notas.html",
        {
            "form_filtro": form_filtro,
            "linhas": linhas,
            "total_alunos": len({linha["aluno"].pk for linha in linhas}),
            "total_avaliadas": sum(linha["total_avaliadas"] for linha in linhas),
            "total_movimentacoes": sum(linha["total_movimentacoes"] for linha in linhas),
            "media_geral_estrelas": media_para_estrelas(media_geral_das_notas(ciclos)),
            "breadcrumbs": [
                home_breadcrumb(request.user),
                {"label": "Relatório de Notas", "url": None},
            ],
        },
    )


@login_required
@exige_permissao(pode_ver_avaliacoes_pendentes)
def avaliacoes_pendentes(request):
    # o painel conta as pendentes dos ciclos em andamento; a tela detalha esse mesmo universo
    ciclos_disponiveis = (
        ciclos_do_avaliador(request.user)
        .filter(status__nome_status__iexact="em andamento")
        .order_by("-ano", "-semestre", "nome_edicao")
    )
    form_filtro, ciclos = _ciclos_filtrados(request, ciclos_disponiveis)

    pendentes = list(movimentacoes_pendentes_de_avaliacao(request.user, ciclos))

    return render(
        request,
        "avaliacoes/avaliacoes_pendentes.html",
        {
            "form_filtro": form_filtro,
            "pendentes": pendentes,
            "total_alunos_aguardando": len({mov.autor_id for mov in pendentes}),
            "mais_antiga": pendentes[0].data_movimento if pendentes else None,
            "breadcrumbs": [
                home_breadcrumb(request.user),
                {"label": "Avaliações Pendentes", "url": None},
            ],
        },
    )
