from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404
from usuarios.models import Usuario

from .forms_admin_usuarios import AtualizarUsuarioForm
from .permissions import tipos_que_pode_atribuir, pode_gerenciar_usuarios



@login_required
def usuario_lista(request):
    if not pode_gerenciar_usuarios(request.user):
        raise Http404()

    if not tipos_que_pode_atribuir(request.user):
        raise Http404()

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
def usuario_atualizar(request):
    if request.method != "POST":
        raise Http404()

    if not pode_gerenciar_usuarios(request.user):
        raise Http404()

    if not tipos_que_pode_atribuir(request.user):
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
        messages.success(request, "Usuario atualizado com sucesso.")
    else:
        for erros in form.errors.values():
            for erro in erros:
                messages.error(request, erro)

    next_url = request.POST.get("next", "")
    if next_url:
        return redirect(next_url)
    return redirect("acesso:usuario_lista")


@login_required
def painel_administrativo(request):
    context = {}
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
    return render(request, "acesso/painel_administrativo.html", context)


