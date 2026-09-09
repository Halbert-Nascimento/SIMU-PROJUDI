from django.urls import path

from .views import editar_movimentacao, movimentar_processo

app_name = "movimentacoes"

urlpatterns = [
    path("<str:numero>/movimentar/<int:mov_id>/", editar_movimentacao, name="editar_movimentacao"),
    path("<str:numero>/movimentar/", movimentar_processo, name="movimentar_processo"),
]
