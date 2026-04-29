from django.urls import path

from .views import cadastrar_processo, varas_por_comarca

app_name = "processos"

urlpatterns = [
    path("cadastrar/", cadastrar_processo, name="cadastrar_processo"),
    path(
        "api/varas/<int:comarca_id>/",
        varas_por_comarca,
        name="varas_por_comarca",
    ),
]
