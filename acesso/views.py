import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from base.breadcrumbs import home_breadcrumb
from base.navegacao import home_do_usuario, tem_tela_inicial
from usuarios.forms import CadastroPublicoForm
from usuarios.models import DATA_VIGENCIA_TERMOS, VERSAO_TERMOS_ATUAL, Usuario

from .forms import AceiteTermosForm, AlterarMinhaSenhaForm, LoginForm


logger = logging.getLogger(__name__)




def login_view(request):
    # base:home também aponta para cá (logo do cabeçalho): quem já entrou vai
    # para a própria tela inicial em vez de rever o formulário de login.
    # Só em GET: o POST segue para o formulário, então trocar de conta sem
    # sair antes continua funcionando. Perfil sem tela inicial (Pendente) vê o
    # formulário como antes, em vez de cair numa tela que o recusa.
    if request.method == "GET" and tem_tela_inicial(request.user):
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


def _contexto_documento_legal(request):
    logado = request.user.is_authenticated
    return {
        # Só serve de reserva: o rodapé (base.html) linka estas páginas a
        # partir de qualquer tela, então "voltar" de verdade é o histórico do
        # navegador (ver onclick em termos_de_uso.html/politica_privacidade.html);
        # este valor só é usado se o visitante chegar sem histórico ou com JS
        # desabilitado.
        "voltar_url": "base:home" if logado else "acesso:cadastro",
        "versao_termos_atual": VERSAO_TERMOS_ATUAL,
        "data_vigencia_termos": DATA_VIGENCIA_TERMOS,
    }


def termos_de_uso(request):
    contexto = _contexto_documento_legal(request)
    return render(request, "acesso/termos_de_uso.html", contexto)


def politica_privacidade(request):
    contexto = _contexto_documento_legal(request)
    return render(request, "acesso/politica_privacidade.html", contexto)


@login_required
def aceite_termos_pendente(request):
    """
    Portão exibido a quem está logado mas não aceitou a versão vigente dos
    Termos de Uso / Política de Privacidade — ver
    `acesso.middleware.TermosAceitosMiddleware`.
    """
    proximo = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        form = AceiteTermosForm(request.POST)
        if form.is_valid():
            request.user.aceitou_termos_em = timezone.now()
            request.user.versao_termos_aceita = VERSAO_TERMOS_ATUAL
            request.user.save(
                update_fields=["aceitou_termos_em", "versao_termos_aceita"]
            )
            logger.info(
                "Termos de Uso versao=%s aceitos por usuario=%s",
                VERSAO_TERMOS_ATUAL, request.user.pk,
            )

            destino = "base:home"
            if proximo and url_has_allowed_host_and_scheme(
                proximo,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                destino = proximo
            return redirect(destino)
    else:
        form = AceiteTermosForm()

    contexto = {"form": form, "next": proximo}
    return render(request, "acesso/aceite_termos_pendente.html", contexto)


@login_required
def minha_conta(request):
    """
    Autoalteração de senha — separada do modal de gestão de usuários porque
    `usuario_atualizar` bloqueia autoedição, e Aluno/Pendente nem acessam aquela tela.
    """
    if request.method == "POST":
        form = AlterarMinhaSenhaForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Sem isto, a próxima requisição derruba a sessão por hash de senha desatualizado.
            update_session_auth_hash(request, request.user)
            messages.success(request, "Senha alterada com sucesso.", extra_tags="conta")
            return redirect("acesso:minha_conta")
        # Sem propagar_erros_form: minha_conta.html já mostra form.<campo>.errors inline,
        # e repetir via messages duplicaria cada erro na tela (banner + campo).
    else:
        form = AlterarMinhaSenhaForm(request.user)

    # base:home substitui a URL de home_breadcrumb(): para Pendente ela apontaria a uma tela que o recusa.
    home = home_breadcrumb(request.user)
    home["url"] = reverse("base:home")

    return render(request, "acesso/minha_conta.html", {
        "form": form,
        "breadcrumbs": [home, {"label": "Minha Conta", "url": None}],
        "home_label": home["label"],
    })
