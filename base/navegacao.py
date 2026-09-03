from __future__ import annotations

from django.urls import reverse

from acesso.permissions import pode_gerenciar_usuarios


def home_do_usuario(user) -> tuple[str, str]:
    """
    Rótulo e URL da tela inicial do perfil, como (label, url).

    Quem entra pelo painel administrativo é exatamente quem pode acessá-lo, então
    a pergunta é feita a `pode_gerenciar_usuarios` em vez de repetir o conjunto de
    perfis aqui — repetir deixaria a navegação apontando para uma tela que a
    guarda da view recusa, que era o caso do perfil Pendente.
    """
    if user is not None and pode_gerenciar_usuarios(user):
        return "Painel Administrativo", reverse("acesso:painel_administrativo")
    return "Área do Servidor", reverse("processos:pagina_aluno")
