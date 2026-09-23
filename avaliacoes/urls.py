from django.urls import path

from .views import avaliar_movimentacao, minhas_notas
from .views_relatorios import avaliacoes_pendentes, relatorio_notas

app_name = "avaliacoes"

urlpatterns = [
    path("minhas-notas/", minhas_notas, name="minhas_notas"),
    path("relatorio-notas/", relatorio_notas, name="relatorio_notas"),
    path("pendentes/", avaliacoes_pendentes, name="avaliacoes_pendentes"),
    path("<int:movimentacao_id>/", avaliar_movimentacao, name="avaliar"),
]
