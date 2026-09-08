from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from base.breadcrumbs import home_breadcrumb

from .models import NOTIFICACOES_RECENTES_LIMIT, Notificacao


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
def contagem_notificacoes(request):
    total_nao_lidas = Notificacao.objects.filter(destinatario=request.user, lida=False).count()
    return JsonResponse({"nao_lidas": total_nao_lidas})


@login_required
@require_POST
def marcar_recentes_como_lidas(request):
    ids_recentes_pendentes = list(
        Notificacao.objects.filter(destinatario=request.user, lida=False)
        .order_by("-data_criacao")
        .values_list("pk", flat=True)[:NOTIFICACOES_RECENTES_LIMIT]
    )
    if ids_recentes_pendentes:
        Notificacao.objects.filter(pk__in=ids_recentes_pendentes).update(lida=True, data_leitura=timezone.now())
    return JsonResponse({"sucesso": True})
