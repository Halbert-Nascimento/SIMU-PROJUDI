from django.urls import path

from .views import criar_ciclo, gerenciar_grupos

app_name = "ciclos"

urlpatterns = [
    path("criar/", criar_ciclo, name="criar_ciclo"),
    path("grupos/gerenciar/", gerenciar_grupos, name="gerenciar_grupos"),
]
