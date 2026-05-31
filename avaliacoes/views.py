from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Max
from django.shortcuts import get_object_or_404, redirect, render

from ciclos.models import GrupoTrabalho
from processos.models import MovimentacaoProcessual

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
            feedback = form.save(commit=False)
            feedback.movimentacao = movimentacao
            feedback.professor = request.user
            if acao == "devolver":
                feedback.nota = None
            feedback.save()

            if acao == "devolver":
                messages.success(request, "Movimentação devolvida para revisão.")
            else:
                messages.success(request, "Avaliação concluída com sucesso.")
            return redirect("processos:visualizar_processo", numero=processo.numero)
        else:
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, erro)
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

    media_notas = (
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
    )

    total_avaliadas = feedbacks.filter(nota__isnull=False).count()
    ultima_avaliacao = feedbacks.first()

    feedbacks_data = []
    for fb in feedbacks:
        mov = fb.movimentacao
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
            "nota": float(fb.nota) if fb.nota is not None else None,
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
            "media_geral": stats["media"],
            "melhor_nota": stats["melhor"],
            "ultima_avaliacao": ultima_avaliacao,
        },
    )
