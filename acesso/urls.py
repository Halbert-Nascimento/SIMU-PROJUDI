from django.urls import path

from .views import (
    aceite_termos_pendente,
    cadastrar,
    login_view,
    logout_view,
    manter_sessao,
    minha_conta,
    politica_privacidade,
    termos_de_uso,
)
from .views_admin_usuarios import usuario_atualizar, usuario_lista, painel_administrativo

app_name = "acesso"

urlpatterns = [

    path("", login_view, name="login"),
    path("sair/", logout_view, name="logout"),
    path("cadastro/", cadastrar, name="cadastro"),
    path("manter-sessao/", manter_sessao, name="manter_sessao"),
    path("minha-conta/", minha_conta, name="minha_conta"),
    path("termos-de-uso/", termos_de_uso, name="termos_de_uso"),
    path("politica-privacidade/", politica_privacidade, name="politica_privacidade"),
    path("aceite-termos/", aceite_termos_pendente, name="aceite_termos_pendente"),

    # Gestão de usuários
    path("usuarios/", usuario_lista, name="usuario_lista"),
    path("usuarios/atualizar/", usuario_atualizar, name="usuario_atualizar"),
    path("painel-administrativo/", painel_administrativo, name="painel_administrativo"),
]
