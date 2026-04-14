from django.urls import path

from .views import gerenciar_grupos

app_name = "ciclos"

urlpatterns = [
    path("grupos/gerenciar/", gerenciar_grupos, name="gerenciar_grupos"),
]
