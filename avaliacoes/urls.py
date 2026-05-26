from django.urls import path

from .views import avaliar_movimentacao

app_name = "avaliacoes"

urlpatterns = [
    path("<int:movimentacao_id>/", avaliar_movimentacao, name="avaliar"),
]
