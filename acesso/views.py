import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from base.navegacao import home_do_usuario
from usuarios.forms import CadastroPublicoForm
from usuarios.models import Usuario

from .forms import LoginForm


logger = logging.getLogger(__name__)




def login_view(request):
    # base:home também aponta para cá (logo do cabeçalho): quem já entrou vai
    # para a própria tela inicial em vez de rever o formulário de login
    if request.user.is_authenticated:
        return redirect(home_do_usuario(request.user)[1])

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and not form.is_valid():
        logger.warning(
            "Tentativa de login invalida para identificador=%s",
            request.POST.get("username") or request.POST.get("email") or "",
        )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        penultimo_login = user.last_login
        login(request, user)
        if penultimo_login:
            request.session['penultimo_login'] = penultimo_login.isoformat()
        else:
            request.session.pop('penultimo_login', None)
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

        return redirect("acesso:login")

    return render(request, "acesso/login.html", {"form": form})





@require_POST
def manter_sessao(request):
    """
    Ping de atividade da tela aberta: o usuário mexeu, a sessão não deve expirar.

    A view não carimba nada — quem carimba é o `SessionActivityMiddleware`, em
    toda requisição que não seja automática. Ela existe para dar ao contador da
    tela um alvo barato, que não recarrega a página nem devolve HTML: antes, o
    "Continuar sessão" era um reload, e levava junto o que estivesse escrito no
    editor.

    Sessão já expirada não chega aqui: o middleware responde o redirecionamento
    para o login antes. Por isso o cliente confere o corpo, e não só o status.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"autenticado": False}, status=401)

    return JsonResponse({
        "autenticado": True,
        "restante": settings.SESSION_COOKIE_AGE,
    })


@require_POST
def logout_view(request):
    auth_logout(request)
    if request.POST.get('exp'):
        return redirect(reverse('acesso:login') + '?exp=1')
    messages.success(request, "Você saiu com sucesso.")
    return redirect("acesso:login")


def cadastrar(request):
    if request.method == "POST":
        form = CadastroPublicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Cadastro realizado com sucesso! Aguarde a aprovação de um responsável para acessar o sistema.",
            )
            return redirect("acesso:login")
    else:
        form = CadastroPublicoForm()

    return render(request, "acesso/cadastro_usuario.html", {"form": form})