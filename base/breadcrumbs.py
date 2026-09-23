from base.navegacao import home_do_usuario


def home_breadcrumb(user):
    """Retorna o item inicial do breadcrumb de acordo com o perfil do usuário."""
    label, url = home_do_usuario(user)
    return {"label": label, "url": url}
