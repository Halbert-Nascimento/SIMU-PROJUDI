from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    DocumentoAnexado,
    MovimentacaoProcessual,
    ProcessoJudicial,
    TipoMovimentacao,
)
from .permissions import pode_visualizar_processo
from .utils import validar_multiplos_arquivos


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _contexto_base(processo):
    """Monta polos e tipos de movimentação para o template."""
    polos = list(processo.polos.all())
    tipos = (
        TipoMovimentacao.objects
        .exclude(nome_movimentacao="Cadastro do Processo")
        .order_by("nome_movimentacao")
    )
    return {
        "processo": processo,
        "polos_ativo":   [p for p in polos if p.tipo_polo == "Ativo"],
        "polos_passivo": [p for p in polos if p.tipo_polo == "Passivo"],
        "tipos_movimentacao": tipos,
    }


def _salvar_movimentacao(request, processo, mov_origem=None):
    """
    Persiste uma nova MovimentacaoProcessual e seus DocumentoAnexado.

    Retorna (mov, erros):
        mov   — objeto criado (ou None se houve erros)
        erros — lista de strings com mensagens de erro
    """
    tipo_id  = request.POST.get("tipo_movimento", "").strip()
    descricao = request.POST.get("descricao_evento", "").strip()
    arquivos_raw = request.FILES.getlist("documentos")
    nomes_docs   = request.POST.getlist("documento_nomes")

    erros: list[str] = []

    if not tipo_id:
        erros.append("Selecione o tipo de movimentação.")

    arquivos_validos: list = []
    if arquivos_raw:
        arquivos_validos, erros_upload = validar_multiplos_arquivos(arquivos_raw, nomes_docs)
        erros.extend(erros_upload)

    if erros:
        return None, erros

    with transaction.atomic():
        antecedente = (
            processo.movimentacoes
            .order_by("-data_movimento")
            .first()
        )

        mov = MovimentacaoProcessual.objects.create(
            processo=processo,
            autor=request.user,
            tipo_movimento_id=tipo_id,
            descricao_evento=descricao,
            antecedente_logico=antecedente,
            movimentacao_origem=mov_origem,
        )

        for arquivo, titulo in arquivos_validos:
            DocumentoAnexado.objects.create(
                movimentacao=mov,
                titulo_arquivo=titulo,
                caminho_arquivo=arquivo,
            )

        editor_html = request.POST.get("editor_html", "").strip()
        editor_nome = request.POST.get("editor_html_nome", "").strip() or "documento_editor"
        if editor_html:
            conteudo = ContentFile(editor_html.encode("utf-8"), name=f"{editor_nome}.html")
            DocumentoAnexado.objects.create(
                movimentacao=mov,
                titulo_arquivo=editor_nome,
                caminho_arquivo=conteudo,
            )

    return mov, []


# ---------------------------------------------------------------------------
# View: nova movimentação
# ---------------------------------------------------------------------------

@login_required
def movimentar_processo(request, numero):
    processo = get_object_or_404(
        ProcessoJudicial.objects
        .select_related(
            "tipo_processo", "classe", "status_atual",
            "vara", "vara__comarca",
        )
        .prefetch_related("polos__parte"),
        numero=numero,
    )

    if not pode_visualizar_processo(request.user, processo):
        raise PermissionDenied

    ctx = _contexto_base(processo)
    ctx["breadcrumbs"] = [
        {"label": "Área do Servidor", "url": reverse("processos:pagina_aluno")},
        {"label": f"Processo {processo.numero}", "url": reverse("processos:visualizar_processo", args=[processo.numero])},
        {"label": "Movimentar", "url": None},
    ]

    if request.method == "POST":
        mov, erros = _salvar_movimentacao(request, processo, mov_origem=None)

        if erros:
            for msg in erros:
                messages.error(request, msg, extra_tags="movimentacao")
            return render(request, "processos/movimentar_processo.html", ctx)

        messages.success(
            request,
            "Movimentação registrada com sucesso.",
            extra_tags="movimentacao",
        )
        return redirect("processos:visualizar_processo", numero=numero)

    return render(request, "processos/movimentar_processo.html", ctx)


# ---------------------------------------------------------------------------
# View: editar movimentação existente
# ---------------------------------------------------------------------------

@login_required
def editar_movimentacao(request, numero, mov_id):
    processo = get_object_or_404(
        ProcessoJudicial.objects
        .select_related(
            "tipo_processo", "classe", "status_atual",
            "vara", "vara__comarca",
        )
        .prefetch_related("polos__parte"),
        numero=numero,
    )

    if not pode_visualizar_processo(request.user, processo):
        raise PermissionDenied

    mov_original = get_object_or_404(
        MovimentacaoProcessual,
        pk=mov_id,
        processo=processo,
    )

    ctx = _contexto_base(processo)
    ctx.update({
        "movimentacao_origem_id": mov_original.pk,
        "edicao_tipo_id":         mov_original.tipo_movimento_id,
        "edicao_descricao":       mov_original.descricao_evento,
        "breadcrumbs": [
            {"label": "Área do Servidor", "url": reverse("processos:pagina_aluno")},
            {"label": f"Processo {processo.numero}", "url": reverse("processos:visualizar_processo", args=[processo.numero])},
            {"label": "Editar Movimentação", "url": None},
        ],
    })

    if request.method == "POST":
        mov, erros = _salvar_movimentacao(request, processo, mov_origem=mov_original)

        if erros:
            for msg in erros:
                messages.error(request, msg, extra_tags="movimentacao")
            return render(request, "processos/movimentar_processo.html", ctx)

        messages.success(
            request,
            "Movimentação editada e nova versão registrada com sucesso.",
            extra_tags="movimentacao",
        )
        return redirect("processos:visualizar_processo", numero=numero)

    return render(request, "processos/movimentar_processo.html", ctx)
