from django.urls import path

from .views import contagem_notificacoes, listar_notificacoes, recentes_notificacoes

app_name = "notificacoes"

urlpatterns = [
    path("", listar_notificacoes, name="listar"),
    path("recentes/", recentes_notificacoes, name="recentes"),
    path("contagem/", contagem_notificacoes, name="contagem"),
]
