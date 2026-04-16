from django.urls import path

from .views import criar_ciclo, detalhe_ciclo, editar_ciclo, gerenciar_grupos

app_name = "ciclos"

urlpatterns = [
    path("criar/", criar_ciclo, name="criar_ciclo"),
    path("<int:ciclo_id>/editar/", editar_ciclo, name="editar_ciclo"),
    path("<int:ciclo_id>/detalhe/", detalhe_ciclo, name="detalhe_ciclo"),
    path("<int:ciclo_id>/grupos/", gerenciar_grupos, name="gerenciar_grupos"),
]
