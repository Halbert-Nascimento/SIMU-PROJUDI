from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from ciclos.models import CicloSimulacao

from .forms import ProcessoJudicialForm
from .models import Comarca, ProcessoJudicial, StatusProcessoJudicial, VaraServentia


@login_required
def cadastrar_processo(request):
    ciclo = (
        CicloSimulacao.objects.filter(
            Q(coordenador=request.user) | Q(participantes=request.user),
            status__nome_status__iexact="em andamento",
        )
        .order_by("-data_criacao")
        .first()
    )

    if not ciclo:
        messages.error(
            request,
            "Nenhum ciclo ativo encontrado para o seu usuário.",
            extra_tags="processo",
        )
        return redirect("acesso:painel_administrativo")

    if request.method == "POST":
        form = ProcessoJudicialForm(request.POST)
        if form.is_valid():
            processo = form.save(commit=False)
            processo.numero = ProcessoJudicial.gerar_numero_unico()
            processo.ciclo = ciclo
            processo.status_atual = StatusProcessoJudicial.objects.first()
            processo.save()
            messages.success(
                request,
                f'Processo "{processo.numero}" cadastrado com sucesso.',
                extra_tags="processo",
            )
            return redirect("processos:cadastrar_processo")
        else:
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, erro, extra_tags="processo")
    else:
        form = ProcessoJudicialForm()

    return render(
        request,
        "processos/cadastro_processo.html",
        {
            "form": form,
            "ciclo": ciclo,
            "comarcas": Comarca.objects.all().order_by("nome"),
        },
    )


@login_required
def varas_por_comarca(request, comarca_id):
    varas = VaraServentia.objects.filter(comarca_id=comarca_id).values("id", "nome")
    return JsonResponse(list(varas), safe=False)
