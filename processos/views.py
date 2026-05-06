from __future__ import annotations

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from ciclos.models import CicloSimulacao

from .forms import ProcessoJudicialForm
from .models import Comarca, ProcessoJudicial, StatusProcessoJudicial, VaraServentia


def _saudacao():
    hora = datetime.datetime.now().hour
    if hora < 12:
        return "Bom Dia"
    if hora < 18:
        return "Boa Tarde"
    return "Boa Noite"


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
def pagina_aluno(request):
    usuario = request.user

    grupo = (
        usuario.grupos_trabalho
        .filter(ciclo__status__nome_status__iexact="em andamento")
        .select_related("cargo_simulacao", "ciclo")
        .first()
    )

    processos = (
        ProcessoJudicial.objects.filter(
            grupos__membros=usuario,
            ciclo__status__nome_status__iexact="em andamento",
        )
        .select_related("classe", "status_atual", "vara", "vara__comarca")
        .distinct()
    )

    serventia = ""
    cargo = ""
    if grupo:
        serventia = grupo.nome
        cargo = grupo.cargo_simulacao.nome

    total_ativos = processos.filter(
        status_atual__nome_status__iexact="ativo",
    ).count()
    total_arquivados = processos.filter(
        status_atual__nome_status__iexact="arquivado",
    ).count()
    total_processos = processos.count()

    return render(
        request,
        "processos/pagina_aluno.html",
        {
            "saudacao": _saudacao(),
            "usuario": usuario,
            "serventia": serventia,
            "cargo": cargo,
            "processos": processos,
            "total_ativos": total_ativos,
            "total_arquivados": total_arquivados,
            "total_processos": total_processos,
        },
    )


@login_required
def varas_por_comarca(request, comarca_id):
    varas = VaraServentia.objects.filter(comarca_id=comarca_id).values("id", "nome")
    return JsonResponse(list(varas), safe=False)
