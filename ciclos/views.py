from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.models import Usuario

from .forms import CicloSimulacaoForm, GrupoTrabalhoForm
from .models import CargoSimulacao, CicloSimulacao, GrupoTrabalho, StatusCiclo
from .permissions import pode_criar_ciclo, pode_editar_ciclo, pode_gerenciar_grupos_ciclo


@login_required
def criar_ciclo(request):
    if not pode_criar_ciclo(request.user):
        raise Http404()

    if request.method != "POST":
        raise Http404()

    form = CicloSimulacaoForm(request.POST)
    if form.is_valid():
        ciclo = form.save(commit=False)
        ciclo.coordenador = request.user
        ciclo.save()
        messages.success(request, f'Ciclo "{ciclo.nome_edicao}" criado com sucesso.')
    else:
        for erros in form.errors.values():
            for erro in erros:
                messages.error(request, erro, extra_tags="ciclo")

    return redirect("acesso:painel_administrativo")


@login_required
def editar_ciclo(request, ciclo_id):
    ciclo = get_object_or_404(
        CicloSimulacao.objects.select_related("status", "coordenador"),
        pk=ciclo_id,
    )

    if not pode_editar_ciclo(request.user, ciclo):
        raise Http404()

    if request.method == "POST":
        form = CicloSimulacaoForm(request.POST, instance=ciclo, ator=request.user)
        if form.is_valid():
            ciclo_salvo = form.save(commit=False)
            if "coordenador" in form.fields:
                ciclo_salvo.coordenador = form.cleaned_data["coordenador"]
            ciclo_salvo.save()
            messages.success(request, f'Ciclo "{ciclo_salvo.nome_edicao}" atualizado com sucesso.')
            return redirect("acesso:painel_administrativo")
        else:
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, erro)
    else:
        form = CicloSimulacaoForm(instance=ciclo, ator=request.user)

    return render(request, "ciclos/editar_ciclo.html", {
        "ciclo": ciclo,
        "form": form,
        "status_ciclo_opcoes": StatusCiclo.objects.all(),
    })


@login_required
def detalhe_ciclo(request, ciclo_id):
    ciclo = get_object_or_404(
        CicloSimulacao.objects
        .select_related("status", "coordenador")
        .prefetch_related("grupos__cargo_simulacao", "grupos__membros"),
        pk=ciclo_id,
    )

    if not pode_criar_ciclo(request.user):
        raise Http404()

    tp = request.user.tipo_perfil_global
    if tp == Usuario.TipoPerfilGlobal.PROFESSOR:
        vinculado = (
            ciclo.coordenador_id == request.user.pk
            or ciclo.participantes.filter(pk=request.user.pk).exists()
        )
        if not vinculado:
            raise Http404()

    grupos = ciclo.grupos.all()
    total_membros = sum(len(g.membros.all()) for g in grupos)

    return render(request, "ciclos/detalhe_ciclo.html", {
        "ciclo": ciclo,
        "grupos": grupos,
        "total_membros": total_membros,
        "pode_editar": pode_editar_ciclo(request.user, ciclo),
    })


@login_required
def gerenciar_grupos(request, ciclo_id):
    ciclo = get_object_or_404(
        CicloSimulacao.objects.select_related("status", "coordenador"),
        pk=ciclo_id,
    )

    if not pode_gerenciar_grupos_ciclo(request.user, ciclo):
        raise Http404()

    grupos = ciclo.grupos.select_related("cargo_simulacao").order_by("nome")
    cargos = CargoSimulacao.objects.all()

    grupo_editando = None
    form = GrupoTrabalhoForm(ciclo=ciclo)
    reabrir_modal = False

    if request.method == "POST":
        grupo_id = request.POST.get("grupo_id") or None
        if grupo_id:
            grupo_editando = get_object_or_404(GrupoTrabalho, pk=grupo_id, ciclo=ciclo)
            form = GrupoTrabalhoForm(request.POST, instance=grupo_editando, ciclo=ciclo)
            acao = "atualizado"
        else:
            form = GrupoTrabalhoForm(request.POST, ciclo=ciclo)
            acao = "criado"

        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.ciclo = ciclo
            grupo.save()
            messages.success(
                request,
                f'Grupo "{grupo.nome}" {acao} com sucesso.',
                extra_tags="grupo",
            )
            return redirect("ciclos:gerenciar_grupos", ciclo_id=ciclo.pk)
        else:
            reabrir_modal = True
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, erro, extra_tags="grupo")

    return render(request, "ciclos/gerenciar_grupos.html", {
        "ciclo": ciclo,
        "grupos": grupos,
        "cargos": cargos,
        "form": form,
        "grupo_editando": grupo_editando,
        "reabrir_modal": reabrir_modal,
    })
