from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404
from django.db.models import Count, Q
from django.utils import timezone

from base.decorators import exige_permissao
from base.mensagens import propagar_erros_form

from usuarios.models import Usuario

from ciclos.models import CicloSimulacao, GrupoTrabalho, ParticipanteCiclo, StatusCiclo
from movimentacoes.models import MovimentacaoProcessual
from processos.models import ProcessoJudicial
from ciclos.permissions import (
    pode_criar_ciclo,
    pode_editar_ciclo,
    pode_ver_todos_ciclos,
    pode_ver_ciclos_arquivados,
)
from .forms_admin_usuarios import AtualizarUsuarioForm
from .permissions import tipos_que_pode_atribuir, pode_gerenciar_usuarios, pode_editar_usuario


def _usuarios_editaveis(ator, usuarios):
    """Pks editáveis por `ator`; autoedição fica fora — as duas telas bloqueiam alterar o próprio usuário."""
    return frozenset(
        u.pk for u in usuarios
        if u.pk != ator.pk and pode_editar_usuario(ator, u)
    )


@login_required
@exige_permissao(pode_gerenciar_usuarios, tipos_que_pode_atribuir)
def usuario_lista(request):
    usuarios = Usuario.objects.order_by("is_active", "tipo_perfil_global", "username")
    tipos_permitidos = tipos_que_pode_atribuir(request.user)
    tipos_opcoes = [
        (tipo.value, tipo.label)
        for tipo in Usuario.TipoPerfilGlobal
        if tipo in tipos_permitidos
    ]
    usuarios_editaveis = _usuarios_editaveis(request.user, usuarios)

    return render(
        request,
        "acesso/usuario_lista.html",
        {
            "usuarios": usuarios,
            "tipos_opcoes": tipos_opcoes,
            "usuarios_editaveis": usuarios_editaveis,
        },
    )


@login_required
@exige_permissao(pode_gerenciar_usuarios, tipos_que_pode_atribuir)
def usuario_atualizar(request):
    if request.method != "POST":
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
        messages.success(request, "Usuario atualizado com sucesso.", extra_tags="usuario")
    else:
        propagar_erros_form(request, form, extra_tags="usuario")

    next_url = request.POST.get("next", "")
    if next_url:
        return redirect(next_url)
    return redirect("acesso:usuario_lista")


@login_required
@exige_permissao(pode_gerenciar_usuarios)
def painel_administrativo(request):
    """
    Tela de entrada de Admin, Coordenador e Professor.

    LIMITE CONHECIDO (decisão consciente, não esquecimento): as listagens abaixo
    — usuários, ciclos e processos dos ciclos em andamento — vêm completas, sem
    Paginator. O template pagina e pesquisa no navegador (`criarPaginador`,
    `filtrarUsuarios`, `filtrarCiclos`), o que exige ter todas as linhas no HTML
    e torna a busca instantânea.

    Os querysets estão certos — `select_related`/`prefetch_related` nos lugares
    certos, sem N+1 —, mas o custo cresce com o tamanho do resultado, não com o
    número de queries: `prefetch_related("polos__parte")` carrega os polos e as
    partes de TODOS os processos ativos a cada requisição. Com o volume atual
    (dezenas de ciclos) isso é irrelevante; com alguns semestres de uso real a
    tela começa a demorar.

    Quando esse ponto chegar, o conserto é mover paginação E busca para o
    servidor: um `Paginator` por listagem, com um parâmetro de página cada
    (`page_processos`, `page_usuarios`, para que paginar uma não reinicie as
    outras) e os termos de busca por querystring. Os contadores
    (`usuarios_pendentes_count`, `total_alunos_vinculados`) devem continuar
    refletindo o total, não a página corrente.
    """
    context = {
        "ano_atual": timezone.localtime().year,
    }

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
        context["usuarios_editaveis"] = _usuarios_editaveis(request.user, usuarios)

    # Os nomes gravados são capitalizados ("Em andamento"); __in seria sensível a caixa fora do MySQL
    status_em_andamento_ou_finalizado = Q(
        status__nome_status__iexact="em andamento"
    ) | Q(status__nome_status__iexact="finalizado")

    if pode_criar_ciclo(request.user):
        context["status_ciclo_opcoes"] = StatusCiclo.objects.all()

        if pode_ver_todos_ciclos(request.user):
            context["ciclos"] = (
                CicloSimulacao.objects
                .select_related("status")
                .annotate(num_grupos=Count("grupos"))
                .filter(status_em_andamento_ou_finalizado)
                .order_by("-data_criacao")
            )
        else:
            # O vínculo de participante entra por subconsulta, não por filtro no
            # M2M: um join em `participantes` multiplicaria as linhas de `grupos`
            # e num_grupos passaria a contar grupos × participantes.
            ciclos_participados = ParticipanteCiclo.objects.filter(
                usuario=request.user
            ).values("ciclo")

            context["ciclos"] = (
                CicloSimulacao.objects
                .select_related("status")
                .annotate(num_grupos=Count("grupos"))
                .filter(
                    Q(coordenador=request.user) | Q(pk__in=ciclos_participados),
                    status_em_andamento_ou_finalizado,
                )
                .order_by("-data_criacao")
            )

    if "ciclos" in context:
        context["ciclos_editaveis"] = frozenset(
            ciclo.pk
            for ciclo in context["ciclos"]
            if pode_editar_ciclo(request.user, ciclo)
        )

    if pode_ver_ciclos_arquivados(request.user):
        context["ciclos_arquivados"] = (
            CicloSimulacao.objects
            .select_related("status", "coordenador")
            .annotate(num_grupos=Count("grupos"))
            .filter(status__nome_status__iexact="arquivado")
            .order_by("-data_criacao")
        )

    if pode_ver_todos_ciclos(request.user):
        ciclos_ativos_professor = list(
            CicloSimulacao.objects
            .filter(status__nome_status__iexact="em andamento")
            .select_related("status")
            .order_by("-data_criacao")
        )
    else:
        ciclos_ativos_professor = list(
            CicloSimulacao.objects
            .filter(
                coordenador=request.user,
                status__nome_status__iexact="em andamento",
            )
            .select_related("status")
            .order_by("-data_criacao")
        )
    context["ciclos_ativos_professor"] = ciclos_ativos_professor
    processos_ativos = (
        ProcessoJudicial.objects
        .filter(ciclo__in=ciclos_ativos_professor)
    )
    context["processos_professor"] = (
        processos_ativos
        .select_related("ciclo", "status_atual", "classe")
        .prefetch_related("polos__parte")
        .order_by("ciclo__nome_edicao", "-data_autuacao")
    )

    # Resumo do Professor inclui ciclos de que participa; a tabela de processos fica só nos que coordena
    ciclos_ativos_resumo = (
        ciclos_ativos_professor
        if pode_ver_todos_ciclos(request.user)
        else request.ciclos_ativos_usuario
    )

    context["processos_ativos_count"] = ProcessoJudicial.objects.filter(
        ciclo__in=ciclos_ativos_resumo
    ).count()
    context["avaliacoes_pendentes_count"] = (
        MovimentacaoProcessual.objects
        .filter(processo__ciclo__in=ciclos_ativos_resumo, feedbacks__isnull=True)
        .count()
    )
    context["grupos_trabalho_count"] = GrupoTrabalho.objects.filter(
        ciclo__in=ciclos_ativos_resumo
    ).count()
    context["total_alunos_vinculados"] = (
        Usuario.objects
        .filter(
            is_active=True,
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
            ciclos_participados__in=ciclos_ativos_resumo,
        )
        .distinct()
        .count()
    )

    return render(request, "acesso/painel_administrativo.html", context)


