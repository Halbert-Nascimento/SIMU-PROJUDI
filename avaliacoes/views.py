from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from base.mensagens import propagar_erros_form

from base.breadcrumbs import home_breadcrumb

from ciclos.models import GrupoTrabalho
from movimentacoes.models import MovimentacaoProcessual

from .estrelas import (
    ESTRELAS_MAX,
    contexto_estrelas,
    faixa_da_estrela,
    media_em_estrelas,
    nota_para_estrelas,
)
from .forms import FeedbackForm
from .models import FeedbackProfessor
from .permissions import pode_avaliar_movimentacao, pode_ver_minhas_notas


@login_required
def avaliar_movimentacao(request, movimentacao_id):
    movimentacao = get_object_or_404(
        MovimentacaoProcessual.objects
        .select_related(
            "tipo_movimento",
            "autor",
            "processo",
            "processo__ciclo",
            "processo__classe",
            "movimentacao_origem",
            "movimentacao_origem__tipo_movimento",
        )
        .prefetch_related("documentos"),
        pk=movimentacao_id,
    )

    if not pode_avaliar_movimentacao(request.user, movimentacao):
        raise PermissionDenied

    processo = movimentacao.processo
    ciclo = processo.ciclo
    autor = movimentacao.autor

    feedback_existente = (
        FeedbackProfessor.objects
        .filter(movimentacao=movimentacao, professor=request.user)
        .first()
    )

    if request.method == "POST":
        form = FeedbackForm(
            request.POST,
            instance=feedback_existente,
            ator=request.user,
            movimentacao=movimentacao,
        )
        acao = request.POST.get("acao", "concluir")

        if form.is_valid():
            # update_or_create em vez de ler-e-gravar: um duplo envio do
            # formulário (clique duplo, F5, aba duplicada) fazia as duas leituras
            # voltarem vazias e criava dois feedbacks para o mesmo par
            # (movimentação, professor), inflando a média em `minhas_notas`.
            FeedbackProfessor.objects.update_or_create(
                movimentacao=movimentacao,
                professor=request.user,
                defaults={
                    "comentario": form.cleaned_data["comentario"],
                    "nota": None if acao == "devolver" else form.cleaned_data.get("nota"),
                },
            )

            if acao == "devolver":
                messages.success(request, "Movimentação devolvida para revisão.")
            else:
                messages.success(request, "Avaliação concluída com sucesso.")
            return redirect("processos:visualizar_processo", numero=processo.numero)
        else:
            propagar_erros_form(request, form)
    else:
        form = FeedbackForm(
            instance=feedback_existente,
            ator=request.user,
            movimentacao=movimentacao,
        )

    grupo_autor = (
        GrupoTrabalho.objects
        .filter(ciclo=ciclo, membros=autor)
        .select_related("cargo_simulacao")
        .first()
    )

    mov_origem = movimentacao.movimentacao_origem
    feedback_origem = None
    if mov_origem:
        feedback_origem = (
            FeedbackProfessor.objects
            .filter(movimentacao=mov_origem)
            .select_related("professor")
            .first()
        )

    historico = (
        FeedbackProfessor.objects
        .filter(
            movimentacao__autor=autor,
            movimentacao__processo__ciclo=ciclo,
        )
        .exclude(movimentacao=movimentacao)
        .select_related(
            "movimentacao__tipo_movimento",
            "movimentacao__processo",
        )
        .order_by("-data_feedback")
    )

    media_notas = media_em_estrelas(
        historico
        .filter(nota__isnull=False)
        .aggregate(media=Avg("nota"))["media"]
    )

    return render(
        request,
        "avaliacoes/avaliar.html",
        {
            "movimentacao": movimentacao,
            "processo": processo,
            "ciclo": ciclo,
            "autor": autor,
            "grupo_autor": grupo_autor,
            "form": form,
            "feedback_existente": feedback_existente,
            "mov_origem": mov_origem,
            "feedback_origem": feedback_origem,
            "historico": historico,
            "media_notas": media_notas,
            "breadcrumbs": [
                home_breadcrumb(request.user),
                {"label": f"Processo {processo.numero}", "url": reverse("processos:visualizar_processo", args=[processo.numero])},
                {"label": "Avaliar Movimentação", "url": None},
            ],
        },
    )


@login_required
def minhas_notas(request):
    if not pode_ver_minhas_notas(request.user):
        raise PermissionDenied

    feedbacks = (
        FeedbackProfessor.objects
        .filter(movimentacao__autor=request.user)
        .select_related(
            "professor",
            "movimentacao__tipo_movimento",
            "movimentacao__processo",
            "movimentacao__processo__ciclo",
        )
        .prefetch_related("movimentacao__documentos")
        .order_by("-data_feedback")
    )

    total_movimentacoes = (
        MovimentacaoProcessual.objects
        .filter(autor=request.user)
        .count()
    )

    stats = feedbacks.filter(nota__isnull=False).aggregate(
        media=Avg("nota"),
        melhor=Max("nota"),
        total=Count("pk"),
    )

    total_avaliadas = stats["total"] or 0
    ultima_avaliacao = feedbacks.first()
    media_geral = media_em_estrelas(stats["media"])
    melhor_avaliacao = nota_para_estrelas(stats["melhor"])
    # Largura da barra de progresso: média sobre o máximo, com teto de 100%
    media_percentual = (
        min(100, round(media_geral * 100 / ESTRELAS_MAX))
        if media_geral is not None else 0
    )

    # só há sete desenhos possíveis (sem nota e 0–5): renderiza cada um uma vez
    estrelas_html_por_valor = {}
    feedbacks_data = []
    for fb in feedbacks:
        mov = fb.movimentacao
        estrelas = nota_para_estrelas(fb.nota)
        if estrelas not in estrelas_html_por_valor:
            estrelas_html_por_valor[estrelas] = render_to_string(
                "avaliacoes/components/_estrelas.html",
                contexto_estrelas(estrelas, herda_cor=True),
            )
        docs = [
            {
                "titulo": d.titulo_arquivo,
                "url": d.caminho_arquivo.url if d.caminho_arquivo else "",
            }
            for d in mov.documentos.all()
        ]
        feedbacks_data.append({
            "id": fb.pk,
            "data": fb.data_feedback.strftime("%d/%m/%Y"),
            "mov": mov.tipo_movimento.nome_movimentacao,
            "mov_texto": mov.descricao_evento,
            "proc": mov.processo.numero,
            "prof": fb.professor.get_full_name() or fb.professor.username,
            "prof_iniciais": (
                (fb.professor.first_name[:1] + fb.professor.last_name[:1]).upper()
                or fb.professor.username[:2].upper()
            ),
            "estrelas": estrelas,
            # o desenho das estrelas sai do mesmo template da tag, não do JS
            "estrelas_html": estrelas_html_por_valor[estrelas],
            "faixa": faixa_da_estrela(estrelas),
            "comentario": fb.comentario,
            "documentos": docs,
        })

    return render(
        request,
        "avaliacoes/minhas_notas.html",
        {
            "feedbacks": feedbacks,
            "feedbacks_json": feedbacks_data,
            "total_movimentacoes": total_movimentacoes,
            "total_avaliadas": total_avaliadas,
            "media_geral": media_geral,
            "media_percentual": media_percentual,
            "melhor_avaliacao": melhor_avaliacao,
            "ultima_avaliacao": ultima_avaliacao,
            "breadcrumbs": [
                home_breadcrumb(request.user),
                {"label": "Minhas Notas", "url": None},
            ],
        },
    )
