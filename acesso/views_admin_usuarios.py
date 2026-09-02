from __future__ import annotations

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404
from django.db.models import Count, Q

from base.decorators import exige_permissao
from base.mensagens import propagar_erros_form

from usuarios.models import Usuario

from ciclos.models import CicloSimulacao, StatusCiclo
from processos.models import ProcessoJudicial
from ciclos.permissions import (
    pode_criar_ciclo,
    pode_editar_ciclo,
    pode_ver_todos_ciclos,
    pode_ver_ciclos_arquivados,
)
from .forms_admin_usuarios import AtualizarUsuarioForm
from .permissions import tipos_que_pode_atribuir, pode_gerenciar_usuarios



@login_required
@exige_permissao(pode_gerenciar_usuarios, tipos_que_pode_atribuir)
def usuario_lista(request):
    usuarios = Usuario.objects.order_by("is_active", "tipo_perfil_global", "username")
    tipos_permitidos = tipos_que_pode_atribuir(request.user)
    tipos_opcoes = [
        (tipo.value, tipo.label)
        for tipo in Usuario.TipoPerfilGlobal
        if tipo in tipos_permitidos
    ]

    return render(
        request,
        "acesso/usuario_lista.html",
        {
            "usuarios": usuarios,
            "tipos_opcoes": tipos_opcoes,
        },
    )


@login_required
@exige_permissao(pode_gerenciar_usuarios, tipos_que_pode_atribuir)
def usuario_atualizar(request):
    if request.method != "POST":
        raise Http404()

    user_id = request.POST.get("user_id")
    if not user_id:
        messages.error(request, "Usuario alvo nao informado.")
        return redirect("acesso:usuario_lista")

    alvo = get_object_or_404(Usuario, pk=user_id)

    if alvo.pk == request.user.pk:
        messages.error(request, "Voce nao pode alterar seu proprio usuario por esta tela.")
        return redirect("acesso:usuario_lista")

    form = AtualizarUsuarioForm(request.POST, ator=request.user, alvo=alvo)
    if form.is_valid():
        form.aplicar()
        messages.success(request, "Usuario atualizado com sucesso.", extra_tags="usuario")
    else:
        propagar_erros_form(request, form, extra_tags="usuario")

    next_url = request.POST.get("next", "")
    if next_url:
        return redirect(next_url)
    return redirect("acesso:usuario_lista")


@login_required
@exige_permissao(pode_gerenciar_usuarios)
def painel_administrativo(request):
    context = {
        "ano_atual": datetime.date.today().year,
    }

    if pode_gerenciar_usuarios(request.user) and tipos_que_pode_atribuir(request.user):
        usuarios = Usuario.objects.order_by("is_active", "tipo_perfil_global", "username")
        tipos_permitidos = tipos_que_pode_atribuir(request.user)
        tipos_opcoes = [
            (tipo.value, tipo.label)
            for tipo in Usuario.TipoPerfilGlobal
            if tipo in tipos_permitidos
        ]
        context["usuarios"] = usuarios
        context["tipos_opcoes"] = tipos_opcoes
        context["usuarios_pendentes_count"] = usuarios.filter(is_active=False).count()

    if pode_criar_ciclo(request.user):
        context["status_ciclo_opcoes"] = StatusCiclo.objects.all()

        if pode_ver_todos_ciclos(request.user):
            context["ciclos"] = (
                CicloSimulacao.objects
                .select_related("status")
                .annotate(num_grupos=Count("grupos"))
                .filter(status__nome_status__in=["em andamento", "finalizado"])
                .order_by("-data_criacao")
            )
        else:
            context["ciclos"] = (
                CicloSimulacao.objects
                .select_related("status")
                .annotate(num_grupos=Count("grupos"))
                .filter(
                    Q(coordenador=request.user) | Q(participantes=request.user),
                    status__nome_status__in=["em andamento", "finalizado"],
                )
                .order_by("-data_criacao")
                .distinct()
            )

    if "ciclos" in context:
        context["ciclos_editaveis"] = frozenset(
            ciclo.pk
            for ciclo in context["ciclos"]
            if pode_editar_ciclo(request.user, ciclo)
        )

    if pode_ver_ciclos_arquivados(request.user):
        context["ciclos_arquivados"] = (
            CicloSimulacao.objects
            .select_related("status", "coordenador")
            .annotate(num_grupos=Count("grupos"))
            .filter(status__nome_status="arquivado")
            .order_by("-data_criacao")
        )

    if pode_ver_todos_ciclos(request.user):
        ciclos_ativos_professor = list(
            CicloSimulacao.objects
            .filter(status__nome_status="em andamento")
            .select_related("status")
            .order_by("-data_criacao")
        )
    else:
        ciclos_ativos_professor = list(
            CicloSimulacao.objects
            .filter(coordenador=request.user, status__nome_status="em andamento")
            .select_related("status")
            .order_by("-data_criacao")
        )
    context["ciclos_ativos_professor"] = ciclos_ativos_professor
    context["processos_professor"] = (
        ProcessoJudicial.objects
        .filter(ciclo__in=ciclos_ativos_professor)
        .select_related("ciclo", "status_atual", "classe")
        .prefetch_related("polos__parte")
        .order_by("ciclo__nome_edicao", "-data_autuacao")
    )

    context["total_alunos_vinculados"] = (
        Usuario.objects
        .filter(
            is_active=True,
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
            ciclos_participados__status__nome_status__in=["em andamento"],
        )
        .distinct()
        .count()
    )

    return render(request, "acesso/painel_administrativo.html", context)


