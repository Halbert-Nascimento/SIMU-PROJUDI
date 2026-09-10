from django.urls import path

from .views import cadastrar, login_view, logout_view, manter_sessao
from .views_admin_usuarios import usuario_atualizar, usuario_lista, painel_administrativo

app_name = "acesso"

urlpatterns = [

    path("", login_view, name="login"),
    path("sair/", logout_view, name="logout"),
    path("cadastro/", cadastrar, name="cadastro"),
    path("manter-sessao/", manter_sessao, name="manter_sessao"),

    # Gestão de usuários
    path("usuarios/", usuario_lista, name="usuario_lista"),
    path("usuarios/atualizar/", usuario_atualizar, name="usuario_atualizar"),
    path("painel-administrativo/", painel_administrativo, name="painel_administrativo"),
]
