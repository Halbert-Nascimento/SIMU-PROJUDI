from __future__ import annotations

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from ciclos.models import CicloSimulacao

from .forms import ProcessoJudicialForm
from .models import (
    Comarca,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
    StatusProcessoJudicial,
    VaraServentia,
)


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

        polo_ativo_ids = [v for v in request.POST.getlist("polo_ativo") if v]
        polo_passivo_ids = [v for v in request.POST.getlist("polo_passivo") if v]

        polo_erro = False
        if not polo_ativo_ids:
            messages.error(request, "Insira pelo menos uma parte no Polo Ativo.", extra_tags="processo")
            polo_erro = True
        if not polo_passivo_ids:
            messages.error(request, "Insira pelo menos uma parte no Polo Passivo.", extra_tags="processo")
            polo_erro = True

        if form.is_valid() and not polo_erro:
            processo = form.save(commit=False)
            processo.numero = ProcessoJudicial.gerar_numero_unico()
            processo.ciclo = ciclo
            processo.status_atual = StatusProcessoJudicial.objects.first()
            processo.save()

            processo.grupos.set(ciclo.grupos.all())

            for tipo_polo, ids in (("Ativo", polo_ativo_ids), ("Passivo", polo_passivo_ids)):
                for parte_id in ids:
                    PoloProcessual.objects.create(
                        processo=processo,
                        parte_id=int(parte_id),
                        tipo_polo=tipo_polo,
                    )
            for parte_id in request.POST.getlist("polo_terceiro"):
                if parte_id:
                    PoloProcessual.objects.create(
                        processo=processo,
                        parte_id=int(parte_id),
                        tipo_polo="Terceiro",
                    )

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

    total_arquivados = processos.filter(
        status_atual__nome_status__iexact="arquivado",
    ).count()
    total_em_andamento = processos.exclude(
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
            "total_em_andamento": total_em_andamento,
            "total_arquivados": total_arquivados,
            "total_processos": total_processos,
        },
    )


@login_required
def varas_por_comarca(request, comarca_id):
    varas = VaraServentia.objects.filter(comarca_id=comarca_id).values("id", "nome")
    return JsonResponse(list(varas), safe=False)


@login_required
def buscar_partes(request):
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    partes = (
        ParteFicticia.objects.filter(
            Q(nome_razao__icontains=q) | Q(cpf_cnpj__icontains=q)
        )
        .values("id", "nome_razao", "cpf_cnpj", "tipo_pessoa")[:20]
    )
    return JsonResponse(list(partes), safe=False)


@login_required
def criar_parte(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    import json
    try:
        dados = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    nome = dados.get("nome_razao", "").strip()
    cpf_cnpj = dados.get("cpf_cnpj", "").strip()
    tipo_pessoa = dados.get("tipo_pessoa", "").strip()

    if not nome or not cpf_cnpj or not tipo_pessoa:
        return JsonResponse({"erro": "Preencha todos os campos."}, status=400)

    if ParteFicticia.objects.filter(cpf_cnpj=cpf_cnpj).exists():
        return JsonResponse({"erro": "Já existe uma parte com este CPF/CNPJ."}, status=400)

    parte = ParteFicticia.objects.create(
        nome_razao=nome,
        cpf_cnpj=cpf_cnpj,
        tipo_pessoa=tipo_pessoa,
    )
    return JsonResponse({
        "id": parte.id,
        "nome_razao": parte.nome_razao,
        "cpf_cnpj": parte.cpf_cnpj,
        "tipo_pessoa": parte.tipo_pessoa,
    })
