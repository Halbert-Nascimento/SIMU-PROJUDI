from django.urls import path

from .views import avaliar_movimentacao, minhas_notas

app_name = "avaliacoes"

urlpatterns = [
    path("minhas-notas/", minhas_notas, name="minhas_notas"),
    path("<int:movimentacao_id>/", avaliar_movimentacao, name="avaliar"),
]
