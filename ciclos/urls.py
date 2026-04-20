from django.urls import path

from .views import (
    adicionar_membro,
    criar_ciclo,
    detalhe_ciclo,
    editar_ciclo,
    gerenciar_grupos,
    remover_membro,
)

app_name = "ciclos"

urlpatterns = [
    path("criar/", criar_ciclo, name="criar_ciclo"),
    path("<int:ciclo_id>/editar/", editar_ciclo, name="editar_ciclo"),
    path("<int:ciclo_id>/detalhe/", detalhe_ciclo, name="detalhe_ciclo"),
    path("<int:ciclo_id>/grupos/", gerenciar_grupos, name="gerenciar_grupos"),
    path(
        "<int:ciclo_id>/grupos/<int:grupo_id>/membros/adicionar/",
        adicionar_membro,
        name="adicionar_membro",
    ),
    path(
        "<int:ciclo_id>/grupos/<int:grupo_id>/membros/<int:usuario_id>/remover/",
        remover_membro,
        name="remover_membro",
    ),
]
