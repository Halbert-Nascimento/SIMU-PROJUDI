from django.urls import reverse

from usuarios.models import Usuario


def home_breadcrumb(user):
    """Retorna o item inicial do breadcrumb de acordo com o perfil do usuário."""
    if user.tipo_perfil_global == Usuario.TipoPerfilGlobal.ALUNO:
        return {"label": "Área do Servidor", "url": reverse("processos:pagina_aluno")}
    return {"label": "Painel Administrativo", "url": reverse("acesso:painel_administrativo")}
