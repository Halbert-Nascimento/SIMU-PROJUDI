import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from usuarios.forms import CadastroPublicoForm
from usuarios.models import Usuario

from .forms import LoginForm


logger = logging.getLogger(__name__)




def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and not form.is_valid():
        logger.warning(
            "Tentativa de login invalida para identificador=%s",
            request.POST.get("username") or request.POST.get("email") or "",
        )

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        logger.info("Login realizado com sucesso para usuario=%s", request.user.pk)

        # todo: redirecionar para pagina de acordo com perfil
        if request.user.tipo_perfil_global == Usuario.TipoPerfilGlobal.ADMIN:
            return redirect("acesso:painel_administrativo")

        if request.user.tipo_perfil_global == Usuario.TipoPerfilGlobal.COORDENADOR:
            return redirect("acesso:painel_administrativo")

        if request.user.tipo_perfil_global == Usuario.TipoPerfilGlobal.PROFESSOR:
            return redirect("acesso:painel_administrativo")

        if request.user.tipo_perfil_global == Usuario.TipoPerfilGlobal.ALUNO:
            return redirect("processos:pagina_aluno")

        return redirect("base:redirecionamento_teste_sucesso")

    return render(request, "acesso/login.html", {"form": form})





@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, "Você saiu com sucesso.")
    return redirect("acesso:login")


def cadastrar(request):
    if request.method == "POST":
        form = CadastroPublicoForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("base:redirecionamento_teste_sucesso")
    else:
        form = CadastroPublicoForm()

    return render(request, "acesso/cadastro_usuario.html", {"form": form})