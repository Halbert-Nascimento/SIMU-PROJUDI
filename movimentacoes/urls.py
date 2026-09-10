from django.urls import path

from .views import criar_movimentacao, editar_movimentacao

app_name = "movimentacoes"

urlpatterns = [
    path("<str:numero>/movimentar/<int:mov_id>/", editar_movimentacao, name="editar_movimentacao"),
    path("<str:numero>/movimentar/", criar_movimentacao, name="criar_movimentacao"),
]
