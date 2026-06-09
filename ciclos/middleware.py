from django.db.models import Q

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
