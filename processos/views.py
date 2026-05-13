from __future__ import annotations

import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ciclos.models import CicloSimulacao, GrupoTrabalho

from .forms import ProcessoJudicialForm
from .models import (
    ClasseProcessual,
    Comarca,
    DocumentoAnexado,
    MovimentacaoProcessual,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
    StatusProcessoJudicial,
    TipoMovimentacao,
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

            grupo_criador = request.user.grupos_trabalho.filter(ciclo=ciclo).first()
            if grupo_criador:
                processo.grupos.add(grupo_criador)

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

            tipo_cadastro, _ = TipoMovimentacao.objects.get_or_create(
                nome_movimentacao="Cadastro do Processo",
            )
            mov_cadastro = MovimentacaoProcessual.objects.create(
                descricao_evento=f'Processo "{processo.numero}" cadastrado.',
                processo=processo,
                autor=request.user,
                tipo_movimento=tipo_cadastro,
            )

            arquivos = request.FILES.getlist("documentos")
            nomes_docs = request.POST.getlist("documento_nomes")
            max_size = 7 * 1024 * 1024

            if arquivos:
                tipo_juntada, _ = TipoMovimentacao.objects.get_or_create(
                    nome_movimentacao="Juntada de Documentos",
                )
                mov_juntada = MovimentacaoProcessual.objects.create(
                    descricao_evento="Documentos anexados ao processo.",
                    processo=processo,
                    autor=request.user,
                    tipo_movimento=tipo_juntada,
                    movimentacao_origem=mov_cadastro,
                )
                for i, arquivo in enumerate(arquivos):
                    if arquivo.size > max_size:
                        continue
                    titulo = (
                        nomes_docs[i].strip()
                        if i < len(nomes_docs) and nomes_docs[i].strip()
                        else arquivo.name
                    )
                    DocumentoAnexado.objects.create(
                        titulo_arquivo=titulo,
                        caminho_arquivo=arquivo,
                        movimentacao=mov_juntada,
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

    serventia = ""
    cargo = ""
    is_serventia = False
    grupos_ciclo = []
    if grupo:
        serventia = grupo.nome
        cargo = grupo.cargo_simulacao.nome
        if grupo.cargo_simulacao.cod == "SC":
            is_serventia = True
            grupos_ciclo = list(
                grupo.ciclo.grupos
                .select_related("cargo_simulacao")
                .order_by("nome")
            )

    if is_serventia:
        processos = (
            ProcessoJudicial.objects.filter(
                ciclo=grupo.ciclo,
            )
            .select_related("classe", "status_atual", "vara", "vara__comarca")
            .prefetch_related("polos__parte")
        )
    else:
        processos = (
            ProcessoJudicial.objects.filter(
                grupos__membros=usuario,
                ciclo__status__nome_status__iexact="em andamento",
            )
            .select_related("classe", "status_atual", "vara", "vara__comarca")
            .prefetch_related("polos__parte")
            .distinct()
        )

    # Filtros
    filtro_numero = request.GET.get("numero", "").strip()
    filtro_classe = request.GET.get("classe", "").strip()
    filtro_situacao = request.GET.get("situacao", "").strip()

    if filtro_numero:
        processos = processos.filter(numero__icontains=filtro_numero)
    if filtro_classe:
        processos = processos.filter(classe_id=filtro_classe)
    if filtro_situacao:
        processos = processos.filter(status_atual_id=filtro_situacao)

    total_processos = processos.count()

    # Paginação
    paginator = Paginator(processos, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.META.get("REMOTE_ADDR", "")

    return render(
        request,
        "processos/pagina_aluno.html",
        {
            "saudacao": _saudacao(),
            "usuario": usuario,
            "serventia": serventia,
            "cargo": cargo,
            "page_obj": page_obj,
            "total_processos": total_processos,
            "ip_acesso": ip,
            "classes": ClasseProcessual.objects.all().order_by("nome"),
            "status_opcoes": StatusProcessoJudicial.objects.all(),
            "filtro_numero": filtro_numero,
            "filtro_classe": filtro_classe,
            "filtro_situacao": filtro_situacao,
            "is_serventia": is_serventia,
            "grupos_ciclo": grupos_ciclo,
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


@login_required
def visualizar_processo(request, processo_id):
    processo = get_object_or_404(
        ProcessoJudicial.objects
        .select_related("classe", "status_atual", "vara", "vara__comarca", "tipo_processo", "ciclo")
        .prefetch_related("polos__parte"),
        pk=processo_id,
    )

    polos_ativo = [p for p in processo.polos.all() if p.tipo_polo == "Ativo"]
    polos_passivo = [p for p in processo.polos.all() if p.tipo_polo == "Passivo"]
    polos_terceiro = [p for p in processo.polos.all() if p.tipo_polo == "Terceiro"]

    grupo_serventia = (
        GrupoTrabalho.objects.filter(
            ciclo=processo.ciclo,
            cargo_simulacao__cod="SC",
        )
        .select_related("cargo_simulacao")
        .first()
    )

    grupos_vinculados = (
        processo.grupos
        .select_related("cargo_simulacao")
        .order_by("nome")
    )

    movimentacoes_qs = list(
        processo.movimentacoes
        .select_related("tipo_movimento", "autor")
        .prefetch_related("documentos")
        .order_by("-data_movimento")
    )

    mov_cadastro = None
    mov_juntada = None
    for mov in movimentacoes_qs:
        if mov.tipo_movimento.nome_movimentacao == "Cadastro do Processo":
            mov_cadastro = mov
        elif (
            mov_cadastro
            and mov.movimentacao_origem_id == mov_cadastro.id
            and mov.tipo_movimento.nome_movimentacao == "Juntada de Documentos"
        ):
            mov_juntada = mov

    skip_ids = set()
    if mov_cadastro:
        skip_ids.add(mov_cadastro.id)
    if mov_juntada:
        skip_ids.add(mov_juntada.id)

    movimentacoes = []
    for mov in movimentacoes_qs:
        if mov.id in skip_ids:
            continue
        movimentacoes.append({
            "nome": mov.tipo_movimento.nome_movimentacao,
            "descricao": mov.descricao_evento,
            "data": mov.data_movimento,
            "autor_nome": mov.autor.get_full_name() or mov.autor.username,
            "documentos": list(mov.documentos.all()),
        })

    if mov_cadastro:
        docs = list(mov_cadastro.documentos.all())
        if mov_juntada:
            docs.extend(list(mov_juntada.documentos.all()))
        movimentacoes.append({
            "nome": "Petição Inicial",
            "descricao": mov_cadastro.descricao_evento,
            "data": mov_cadastro.data_movimento,
            "autor_nome": mov_cadastro.autor.get_full_name() or mov_cadastro.autor.username,
            "documentos": docs,
        })

    return render(
        request,
        "processos/visualizar_processo.html",
        {
            "processo": processo,
            "polos_ativo": polos_ativo,
            "polos_passivo": polos_passivo,
            "polos_terceiro": polos_terceiro,
            "grupo_serventia": grupo_serventia,
            "grupos_vinculados": grupos_vinculados,
            "movimentacoes": movimentacoes,
        },
    )


@login_required
@require_POST
def atribuir_grupo_processos(request):
    try:
        dados = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    processo_ids = dados.get("processo_ids", [])
    grupo_ids = dados.get("grupo_ids", [])

    if not processo_ids:
        return JsonResponse({"erro": "Nenhum processo selecionado."}, status=400)

    grupo_usuario = (
        request.user.grupos_trabalho
        .filter(
            ciclo__status__nome_status__iexact="em andamento",
            cargo_simulacao__cod="SC",
        )
        .first()
    )
    if not grupo_usuario:
        return JsonResponse({"erro": "Permissão negada."}, status=403)

    processos = ProcessoJudicial.objects.filter(
        pk__in=processo_ids,
        ciclo=grupo_usuario.ciclo,
    )

    if grupo_ids:
        grupos = GrupoTrabalho.objects.filter(
            pk__in=grupo_ids,
            ciclo=grupo_usuario.ciclo,
        )
        for processo in processos:
            processo.grupos.add(*grupos)
    else:
        for processo in processos:
            processo.grupos.clear()

    return JsonResponse({"sucesso": True, "atualizados": processos.count()})
