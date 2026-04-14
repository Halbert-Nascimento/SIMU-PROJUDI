from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import CicloSimulacaoForm
from .permissions import pode_criar_ciclo


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
def gerenciar_grupos(request):
    nome_ciclo = request.GET.get("ciclo", "")
    return render(request, "ciclos/gerenciar_grupos.html", {"nome_ciclo": nome_ciclo})
