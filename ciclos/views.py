from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from base.breadcrumbs import home_breadcrumb
from django.views.decorators.http import require_POST

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

    post_data = request.POST.copy()
    status_em_andamento = StatusCiclo.objects.filter(
        nome_status__iexact="em andamento"
    ).first()
    if status_em_andamento:
        post_data["status"] = status_em_andamento.pk

    form = CicloSimulacaoForm(post_data)
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
        "breadcrumbs": [
            home_breadcrumb(request.user),
            {"label": ciclo.nome_edicao, "url": reverse("ciclos:detalhe_ciclo", args=[ciclo.pk])},
            {"label": "Editar Ciclo", "url": None},
        ],
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
        "breadcrumbs": [
            home_breadcrumb(request.user),
            {"label": ciclo.nome_edicao, "url": None},
        ],
    })


@login_required
def gerenciar_grupos(request, ciclo_id):
    ciclo = get_object_or_404(
        CicloSimulacao.objects.select_related("status", "coordenador"),
        pk=ciclo_id,
    )

    if not pode_gerenciar_grupos_ciclo(request.user, ciclo):
        raise Http404()

    grupos = list(
        ciclo.grupos
        .select_related("cargo_simulacao")
        .prefetch_related("membros")
        .order_by("nome")
    )
    cargos = CargoSimulacao.objects.all()

    # Alunos ativos não vinculados a nenhum grupo deste ciclo
    alunos_disponiveis = list(
        Usuario.objects
        .filter(is_active=True, tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO)
        .exclude(grupos_trabalho__ciclo=ciclo)
        .order_by("first_name", "last_name", "username")
    )

    total_alunos_ativos = Usuario.objects.filter(
        is_active=True,
        tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
    ).count()

    # Serialização segura para o JS (usa json_script no template)
    membros_por_grupo = {
        str(grupo.pk): [
            {
                "id": m.pk,
                "nome": m.get_full_name().strip() or m.username,
                "matricula": m.username,
            }
            for m in grupo.membros.all()  # usa cache do prefetch_related
        ]
        for grupo in grupos
    }

    alunos_lista = [
        {
            "id": a.pk,
            "nome": a.get_full_name().strip() or a.username,
            "matricula": a.username,
        }
        for a in alunos_disponiveis
    ]

    grupo_editando = None
    form = GrupoTrabalhoForm(ciclo=ciclo)
    reabrir_modal = False

    if request.method == "POST":
        grupo_id_post = request.POST.get("grupo_id") or None
        if grupo_id_post:
            grupo_editando = get_object_or_404(GrupoTrabalho, pk=grupo_id_post, ciclo=ciclo)
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
        "membros_por_grupo": membros_por_grupo,
        "alunos_lista": alunos_lista,
        "total_alunos_ativos": total_alunos_ativos,
        "breadcrumbs": [
            home_breadcrumb(request.user),
            {"label": ciclo.nome_edicao, "url": reverse("ciclos:detalhe_ciclo", args=[ciclo.pk])},
            {"label": "Gerenciar Grupos", "url": None},
        ],
    })


@login_required
@require_POST
def adicionar_membro(request, ciclo_id, grupo_id):
    ciclo = get_object_or_404(CicloSimulacao, pk=ciclo_id)
    grupo = get_object_or_404(GrupoTrabalho, pk=grupo_id, ciclo=ciclo)

    if not pode_gerenciar_grupos_ciclo(request.user, ciclo):
        return JsonResponse({"erro": "Permissão negada."})

    try:
        usuario = Usuario.objects.get(
            pk=request.POST.get("usuario_id"),
            is_active=True,
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
        )
    except (Usuario.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"erro": "Usuário não encontrado ou perfil não é Aluno ativo."})

    # Unicidade: não pode estar em outro grupo do mesmo ciclo
    if GrupoTrabalho.objects.filter(ciclo=ciclo, membros=usuario).exclude(pk=grupo.pk).exists():
        nome = usuario.get_full_name().strip() or usuario.username
        return JsonResponse({"erro": f'"{nome}" já está em outro grupo neste ciclo.'})

    if grupo.membros.filter(pk=usuario.pk).exists():
        return JsonResponse({"erro": "Este aluno já é membro deste grupo."})

    with transaction.atomic():
        grupo.membros.add(usuario)
        ciclo.participantes.add(usuario)  # sincroniza participação no ciclo

    return JsonResponse({
        "sucesso": True,
        "membro": {
            "id": usuario.pk,
            "nome": usuario.get_full_name().strip() or usuario.username,
            "matricula": usuario.username,
        },
    })


@login_required
@require_POST
def remover_membro(request, ciclo_id, grupo_id, usuario_id):
    ciclo = get_object_or_404(CicloSimulacao, pk=ciclo_id)
    grupo = get_object_or_404(GrupoTrabalho, pk=grupo_id, ciclo=ciclo)

    if not pode_gerenciar_grupos_ciclo(request.user, ciclo):
        return JsonResponse({"erro": "Permissão negada."})

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({"erro": "Usuário não encontrado."})

    if not grupo.membros.filter(pk=usuario.pk).exists():
        return JsonResponse({"erro": "Este aluno não é membro deste grupo."})

    with transaction.atomic():
        grupo.membros.remove(usuario)
        # remover_do_ciclo=True se o aluno não pertence a nenhum outro grupo deste ciclo
        remover_do_ciclo = not GrupoTrabalho.objects.filter(
            ciclo=ciclo, membros=usuario
        ).exists()
        if remover_do_ciclo:
            ciclo.participantes.remove(usuario)

    return JsonResponse({"sucesso": True, "removido_do_ciclo": remover_do_ciclo})
