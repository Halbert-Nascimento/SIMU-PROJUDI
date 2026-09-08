from django.urls import path

from .views import contagem_notificacoes, listar_notificacoes, marcar_recentes_como_lidas

app_name = "notificacoes"

urlpatterns = [
    path("", listar_notificacoes, name="listar"),
    path("contagem/", contagem_notificacoes, name="contagem"),
    path("marcar-recentes-lidas/", marcar_recentes_como_lidas, name="marcar_recentes_lidas"),
]
