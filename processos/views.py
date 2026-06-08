from __future__ import annotations

import datetime
import json

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from base.breadcrumbs import home_breadcrumb
from django.views.decorators.http import require_POST

from ciclos.models import CicloSimulacao, GrupoTrabalho

from usuarios.models import Usuario

from .forms import ProcessoJudicialForm
from .permissions import pode_visualizar_processo
from .utils import validar_multiplos_arquivos
from .models import (
    ClasseProcessual,
    Comarca,
    DocumentoAnexado,
    MovimentacaoProcessual,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
    StatusProcessoJudicial,
    TipoMovimentacao,
    VaraServentia,
)


def _saudacao():
    hora = datetime.datetime.now().hour
    if hora < 12:
        return "Bom Dia"
    if hora < 18:
        return "Boa Tarde"
    return "Boa Noite"


def _upload_ctx() -> dict:
    """Retorna as constantes de upload do settings para uso nos templates."""
    cfg = getattr(django_settings, "UPLOAD_CONFIG", {})
    exts = cfg.get("ALLOWED_EXTENSIONS", [".pdf", ".docx", ".jpg", ".jpeg"])
    return {
        "upload_max_mb": cfg.get("MAX_FILE_SIZE_MB", 7),
        "upload_allowed_extensions_json": json.dumps(exts),
        "upload_accept_attr": ",".join(exts),
    }


@login_required
def cadastrar_processo(request):
    ciclo = (
        CicloSimulacao.objects.filter(
            Q(coordenador=request.user) | Q(participantes=request.user),
            status__nome_status__iexact="em andamento",
        )
        .order_by("-data_criacao")
        .first()
    )

    if not ciclo:
        messages.error(
            request,
            "Nenhum ciclo ativo encontrado para o seu usuário.",
            extra_tags="processo",
        )
        return redirect("acesso:painel_administrativo")

    # Listas usadas tanto no POST (erro) quanto no GET (vazias)
    polo_ativo_partes: list = []
    polo_passivo_partes: list = []
    polo_terceiro_partes: list = []

    if request.method == "POST":
        form = ProcessoJudicialForm(request.POST)

        polo_ativo_ids   = [v for v in request.POST.getlist("polo_ativo")    if v]
        polo_passivo_ids = [v for v in request.POST.getlist("polo_passivo")  if v]
        polo_terceiro_ids = [v for v in request.POST.getlist("polo_terceiro") if v]

        # Validação de polos (passo 1) — separada da validação de arquivos (passo 2)
        polo_erro = False
        if not polo_ativo_ids:
            messages.error(request, "Insira pelo menos uma parte no Polo Ativo.", extra_tags="processo")
            polo_erro = True
        if not polo_passivo_ids:
            messages.error(request, "Insira pelo menos uma parte no Polo Passivo.", extra_tags="processo")
            polo_erro = True

        # Validação de arquivos (passo 2) — feita antes da transação
        arquivos_raw = request.FILES.getlist("documentos")
        nomes_docs   = request.POST.getlist("documento_nomes")
        arquivos_validos: list = []
        arquivo_erro = False
        if arquivos_raw:
            arquivos_validos, erros_upload = validar_multiplos_arquivos(arquivos_raw, nomes_docs)
            for msg in erros_upload:
                messages.error(request, msg, extra_tags="processo arquivo")
            if erros_upload:
                arquivo_erro = True

        tem_erro = polo_erro or arquivo_erro or not form.is_valid()

        if not tem_erro:
            try:
                status_autuado = StatusProcessoJudicial.objects.get(
                    nome_status__iexact="Autuado"
                )
            except StatusProcessoJudicial.DoesNotExist:
                messages.error(
                    request,
                    'Status "Autuado" não encontrado. Contate o administrador do sistema.',
                    extra_tags="processo",
                )
                return render(
                    request,
                    "processos/cadastro_processo.html",
                    {"form": form, "ciclo": ciclo, "comarcas": Comarca.objects.all().order_by("nome"),
                     "step_inicial": 1, **_upload_ctx(),
                     "polo_ativo_partes": [], "polo_passivo_partes": [], "polo_terceiro_partes": []},
                )

            with transaction.atomic():
                processo = form.save(commit=False)
                processo.numero = ProcessoJudicial.gerar_numero_cnj(
                    ano=datetime.datetime.now().year,
                    tr=26,
                    origem=processo.vara.comarca_id,
                )
                processo.ciclo = ciclo
                processo.status_atual = status_autuado
                processo.save()

                grupo_criador = request.user.grupos_trabalho.filter(ciclo=ciclo).first()
                if grupo_criador:
                    processo.grupos.add(grupo_criador)

                for tipo_polo, ids in (("Ativo", polo_ativo_ids), ("Passivo", polo_passivo_ids)):
                    for parte_id in ids:
                        PoloProcessual.objects.create(
                            processo=processo,
                            parte_id=int(parte_id),
                            tipo_polo=tipo_polo,
                        )
                for parte_id in polo_terceiro_ids:
                    PoloProcessual.objects.create(
                        processo=processo,
                        parte_id=int(parte_id),
                        tipo_polo="Terceiro",
                    )

                tipo_cadastro, _ = TipoMovimentacao.objects.get_or_create(
                    nome_movimentacao="Cadastro do Processo",
                )
                mov_cadastro = MovimentacaoProcessual.objects.create(
                    descricao_evento=f'Processo "{processo.numero}" cadastrado.',
                    processo=processo,
                    autor=request.user,
                    tipo_movimento=tipo_cadastro,
                )

                for arquivo, titulo in arquivos_validos:
                    DocumentoAnexado.objects.create(
                        titulo_arquivo=titulo,
                        caminho_arquivo=arquivo,
                        movimentacao=mov_cadastro,
                    )

            messages.success(
                request,
                f'Processo "{processo.numero}" cadastrado com sucesso.',
                extra_tags="processo",
            )
            return redirect("processos:cadastrar_processo")
        else:
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, erro, extra_tags="processo")

            # Restaura os polos no contexto para re-renderização com os dados preservados
            if polo_ativo_ids:
                polo_ativo_partes = list(ParteFicticia.objects.filter(id__in=polo_ativo_ids))
            if polo_passivo_ids:
                polo_passivo_partes = list(ParteFicticia.objects.filter(id__in=polo_passivo_ids))
            if polo_terceiro_ids:
                polo_terceiro_partes = list(ParteFicticia.objects.filter(id__in=polo_terceiro_ids))

        # Determina em qual passo abrir o formulário ao reexibir com erros:
        # passo 2 apenas quando o formulário e os polos estão OK e só os arquivos falharam
        step_inicial = 2 if (arquivo_erro and not polo_erro and form.is_valid()) else 1
    else:
        form = ProcessoJudicialForm()
        step_inicial = 1

    return render(
        request,
        "processos/cadastro_processo.html",
        {
            "form": form,
            "ciclo": ciclo,
            "comarcas": Comarca.objects.all().order_by("nome"),
            "step_inicial": step_inicial,
            "polo_ativo_partes": polo_ativo_partes,
            "polo_passivo_partes": polo_passivo_partes,
            "polo_terceiro_partes": polo_terceiro_partes,
            **_upload_ctx(),
        },
    )


@login_required
def pagina_aluno(request):
    usuario = request.user

    grupo = (
        usuario.grupos_trabalho
        .filter(ciclo__status__nome_status__iexact="em andamento")
        .select_related("cargo_simulacao", "ciclo")
        .first()
    )

    serventia = ""
    cargo = ""
    is_serventia = False
    grupos_ciclo = []
    if grupo:
        serventia = grupo.nome
        cargo = grupo.cargo_simulacao.nome
        if grupo.cargo_simulacao.cod == "SC":
            is_serventia = True
            grupos_ciclo = list(
                grupo.ciclo.grupos
                .select_related("cargo_simulacao")
                .order_by("nome")
            )

    if is_serventia:
        processos = (
            ProcessoJudicial.objects.filter(
                ciclo=grupo.ciclo,
            )
            .select_related("classe", "status_atual", "vara", "vara__comarca")
            .prefetch_related("polos__parte")
        )
    else:
        processos = (
            ProcessoJudicial.objects.filter(
                grupos__membros=usuario,
                ciclo__status__nome_status__iexact="em andamento",
            )
            .select_related("classe", "status_atual", "vara", "vara__comarca")
            .prefetch_related("polos__parte")
            .distinct()
        )

    # Filtros
    filtro_numero = request.GET.get("numero", "").strip()
    filtro_classe = request.GET.get("classe", "").strip()
    filtro_situacao = request.GET.get("situacao", "").strip()

    if filtro_numero:
        processos = processos.filter(numero__icontains=filtro_numero)
    if filtro_classe:
        processos = processos.filter(classe_id=filtro_classe)
    if filtro_situacao:
        processos = processos.filter(status_atual_id=filtro_situacao)

    total_processos = processos.count()

    # Paginação
    paginator = Paginator(processos, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.META.get("REMOTE_ADDR", "")

    return render(
        request,
        "processos/pagina_aluno.html",
        {
            "saudacao": _saudacao(),
            "usuario": usuario,
            "serventia": serventia,
            "cargo": cargo,
            "page_obj": page_obj,
            "total_processos": total_processos,
            "ip_acesso": ip,
            "classes": ClasseProcessual.objects.all().order_by("nome"),
            "status_opcoes": StatusProcessoJudicial.objects.all(),
            "filtro_numero": filtro_numero,
            "filtro_classe": filtro_classe,
            "filtro_situacao": filtro_situacao,
            "is_serventia": is_serventia,
            "grupos_ciclo": grupos_ciclo,
        },
    )


@login_required
def varas_por_comarca(request, comarca_id):
    varas = VaraServentia.objects.filter(comarca_id=comarca_id).values("id", "nome")
    return JsonResponse(list(varas), safe=False)


@login_required
def buscar_partes(request):
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    partes = (
        ParteFicticia.objects.filter(
            Q(nome_razao__icontains=q) | Q(cpf_cnpj__icontains=q)
        )
        .values("id", "nome_razao", "cpf_cnpj", "tipo_pessoa")[:20]
    )
    return JsonResponse(list(partes), safe=False)


@login_required
def criar_parte(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    import json
    try:
        dados = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    nome = dados.get("nome_razao", "").strip()
    cpf_cnpj = dados.get("cpf_cnpj", "").strip()
    tipo_pessoa = dados.get("tipo_pessoa", "").strip()

    if not nome or not cpf_cnpj or not tipo_pessoa:
        return JsonResponse({"erro": "Preencha todos os campos."}, status=400)

    if ParteFicticia.objects.filter(cpf_cnpj=cpf_cnpj).exists():
        return JsonResponse({"erro": "Já existe uma parte com este CPF/CNPJ."}, status=400)

    parte = ParteFicticia.objects.create(
        nome_razao=nome,
        cpf_cnpj=cpf_cnpj,
        tipo_pessoa=tipo_pessoa,
    )
    return JsonResponse({
        "id": parte.id,
        "nome_razao": parte.nome_razao,
        "cpf_cnpj": parte.cpf_cnpj,
        "tipo_pessoa": parte.tipo_pessoa,
    })


def visualizar_processo(request, numero):
    processo = get_object_or_404(
        ProcessoJudicial.objects
        .select_related("classe", "status_atual", "vara", "vara__comarca", "tipo_processo", "ciclo")
        .prefetch_related("polos__parte"),
        numero=numero,
    )

    if not pode_visualizar_processo(request.user, processo):
        raise PermissionDenied

    polos_ativo = [p for p in processo.polos.all() if p.tipo_polo == "Ativo"]
    polos_passivo = [p for p in processo.polos.all() if p.tipo_polo == "Passivo"]
    polos_terceiro = [p for p in processo.polos.all() if p.tipo_polo == "Terceiro"]

    grupo_serventia = (
        GrupoTrabalho.objects.filter(
            ciclo=processo.ciclo,
            cargo_simulacao__cod="SC",
        )
        .select_related("cargo_simulacao")
        .first()
    )

    grupos_vinculados = (
        processo.grupos
        .select_related("cargo_simulacao")
        .order_by("nome")
    )

    movimentacoes_qs = list(
        processo.movimentacoes
        .select_related("tipo_movimento", "autor")
        .prefetch_related("documentos")
        .order_by("-data_movimento")
    )

    mov_ids = [m.id for m in movimentacoes_qs]
    from avaliacoes.services import feedbacks_ids_para_movimentacoes
    feedbacks_existentes = feedbacks_ids_para_movimentacoes(mov_ids)

    mov_cadastro = next(
        (m for m in movimentacoes_qs if m.tipo_movimento.nome_movimentacao == "Cadastro do Processo"),
        None,
    )

    skip_ids = {mov_cadastro.id} if mov_cadastro else set()

    movimentacoes = []
    for mov in movimentacoes_qs:
        if mov.id in skip_ids:
            continue
        movimentacoes.append({
            "id": mov.id,
            "autor_id": mov.autor_id,
            "nome": mov.tipo_movimento.nome_movimentacao,
            "descricao": mov.descricao_evento,
            "data": mov.data_movimento,
            "autor_nome": mov.autor.get_full_name() or mov.autor.username,
            "documentos": list(mov.documentos.all()),
            "tem_feedback": mov.id in feedbacks_existentes,
        })

    if mov_cadastro:
        movimentacoes.append({
            "id": mov_cadastro.id,
            "autor_id": mov_cadastro.autor_id,
            "nome": "Petição Inicial",
            "descricao": mov_cadastro.descricao_evento,
            "data": mov_cadastro.data_movimento,
            "autor_nome": mov_cadastro.autor.get_full_name() or mov_cadastro.autor.username,
            "documentos": list(mov_cadastro.documentos.all()),
            "tem_feedback": mov_cadastro.id in feedbacks_existentes,
        })

    from avaliacoes.permissions import perfil_pode_avaliar
    pode_avaliar = perfil_pode_avaliar(request.user)

    return render(
        request,
        "processos/visualizar_processo.html",
        {
            "processo": processo,
            "polos_ativo": polos_ativo,
            "polos_passivo": polos_passivo,
            "polos_terceiro": polos_terceiro,
            "grupo_serventia": grupo_serventia,
            "grupos_vinculados": grupos_vinculados,
            "movimentacoes": movimentacoes,
            "pode_avaliar": pode_avaliar,
            "breadcrumbs": [
                home_breadcrumb(request.user),
                {"label": f"Processo {processo.numero}", "url": None},
            ],
        },
    )


@login_required
@require_POST
def atribuir_grupo_processos(request):
    try:
        dados = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    processo_ids = dados.get("processo_ids", [])
    grupo_ids = dados.get("grupo_ids", [])

    if not processo_ids:
        return JsonResponse({"erro": "Nenhum processo selecionado."}, status=400)

    grupo_usuario = (
        request.user.grupos_trabalho
        .filter(
            ciclo__status__nome_status__iexact="em andamento",
            cargo_simulacao__cod="SC",
        )
        .first()
    )
    if not grupo_usuario:
        return JsonResponse({"erro": "Permissão negada."}, status=403)

    processos = ProcessoJudicial.objects.filter(
        pk__in=processo_ids,
        ciclo=grupo_usuario.ciclo,
    )

    if grupo_ids:
        grupos = GrupoTrabalho.objects.filter(
            pk__in=grupo_ids,
            ciclo=grupo_usuario.ciclo,
        )
        for processo in processos:
            processo.grupos.add(*grupos)
    else:
        for processo in processos:
            processo.grupos.clear()

    return JsonResponse({"sucesso": True, "atualizados": processos.count()})

