from django.db.models import Q
from django.shortcuts import redirect

from .permissions import aguarda_vinculo_a_ciclo

CICLO_SESSION_KEY = "ciclo_ativo_id"


class CicloAtivoMiddleware:
    """
    Resolve o ciclo ativo do usuário a partir da sessão.

    Após execução, disponibiliza em cada request:
      - request.ciclo_ativo          → CicloSimulacao selecionado ou None
      - request.ciclos_ativos_usuario → lista de todos os ciclos "em andamento" do usuário

    Regras:
      - Usuário não autenticado: ambos ficam vazios/None.
      - Sessão tem ciclo_id válido: usa esse ciclo.
      - Sessão tem ciclo_id inválido (expirou/saiu): limpa sessão e reavalia.
      - Exatamente 1 ciclo ativo: auto-seleciona e persiste na sessão.
      - 2+ ciclos ativos e nenhum na sessão: ciclo_ativo = None (view decide o que fazer).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.ciclo_ativo = None
        request.ciclos_ativos_usuario = []

        if request.user.is_authenticated:
            self._resolver_ciclo(request)

        return self.get_response(request)

    def _resolver_ciclo(self, request):
        from .models import CicloSimulacao

        ciclos_ativos = list(
            CicloSimulacao.objects.filter(
                Q(coordenador=request.user) | Q(participantes=request.user),
                status__nome_status__iexact="em andamento",
            )
            .select_related("status")
            .distinct()
        )
        request.ciclos_ativos_usuario = ciclos_ativos

        ciclo_id = request.session.get(CICLO_SESSION_KEY)

        if ciclo_id:
            ciclo = next((c for c in ciclos_ativos if c.pk == ciclo_id), None)
            if ciclo:
                request.ciclo_ativo = ciclo
                return
            # Ciclo salvo na sessão não é mais válido — limpa e continua
            del request.session[CICLO_SESSION_KEY]

        # Auto-seleciona quando há exatamente 1 ciclo ativo (transparente para o usuário)
        if len(ciclos_ativos) == 1:
            request.ciclo_ativo = ciclos_ativos[0]
            request.session[CICLO_SESSION_KEY] = ciclos_ativos[0].pk


class AlunoSemCicloMiddleware:
    """
    Prende na tela de boas-vindas o Aluno que ainda não foi posto em nenhum
    ciclo em andamento.

    É middleware, e não guarda de view, porque a regra não é de uma tela: sem
    ciclo o aluno não tem processo, grupo nem nota, e cada tela que ele
    alcançasse responderia 404 ou uma listagem vazia. Hoje ele chega a um 404 —
    `pagina_aluno` o manda para `selecionar_ciclo`, que sem ciclo nenhum o manda
    para o painel administrativo, que o perfil Aluno não pode abrir.

    Roda depois do `CicloAtivoMiddleware`, de quem herda `ciclos_ativos_usuario`:
    refazer a consulta aqui a cobraria duas vezes por requisição.

    A decisão fica em `process_view` porque é lá que `resolver_match` já existe.
    Liberar por nome de rota, e não por prefixo de caminho, evita que mudar uma
    URL abra silenciosamente um buraco na regra.
    """

    # O cabeçalho continua inteiro na tela de espera: sair tem que funcionar, e
    # o sino é por onde chega o aviso de mudança de status do ciclo.
    ROTAS_LIBERADAS = frozenset({
        "ciclos:boas_vindas",
        "acesso:logout",
        "notificacoes:listar",
        "notificacoes:contagem",
        "notificacoes:marcar_recentes_lidas",
    })

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not aguarda_vinculo_a_ciclo(request.user,
                                       getattr(request, "ciclos_ativos_usuario", [])):
            return None

        rota = getattr(request.resolver_match, "view_name", "")
        if rota in self.ROTAS_LIBERADAS:
            return None

        return redirect("ciclos:boas_vindas")
