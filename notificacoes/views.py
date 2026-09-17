from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from base.breadcrumbs import home_breadcrumb

from .models import Notificacao
from .services import notificacoes_recentes_de


@login_required
def listar_notificacoes(request):
    notificacoes_do_usuario = Notificacao.objects.filter(destinatario=request.user).order_by("-data_criacao")
    paginator = Paginator(notificacoes_do_usuario, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    ids_pendentes = [n.pk for n in page_obj if not n.lida]
    if ids_pendentes:
        Notificacao.objects.filter(pk__in=ids_pendentes).update(lida=True, data_leitura=timezone.now())

    return render(request, "notificacoes/listar_notificacoes.html", {
        "page_obj": page_obj,
        "breadcrumbs": [
            home_breadcrumb(request.user),
            {"label": "Notificações", "url": None},
        ],
    })


@login_required
@require_POST
def recentes_notificacoes(request):
    """
    Conteúdo do dropdown do sino: busca com o `lida` atual (pro destaque) e só
    então marca como lidas. Sem `request=` no render_to_string — é fragmento
    isolado, não precisa dos context processors globais (evita 2 queries à toa).
    """
    notificacoes = list(notificacoes_recentes_de(request.user))
    ids_pendentes = [n.pk for n in notificacoes if not n.lida]
    if ids_pendentes:
        Notificacao.objects.filter(pk__in=ids_pendentes).update(lida=True, data_leitura=timezone.now())
    html = render_to_string("notificacoes/dropdown_conteudo.html", {"notificacoes_recentes": notificacoes})
    return HttpResponse(html)


@login_required
def contagem_notificacoes(request):
    total_nao_lidas = Notificacao.objects.filter(destinatario=request.user, lida=False).count()
    return JsonResponse({"nao_lidas": total_nao_lidas})
