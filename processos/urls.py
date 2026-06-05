from django.urls import path

from .views import (
    atribuir_grupo_processos,
    buscar_partes,
    cadastrar_processo,
    criar_parte,
    pagina_aluno,
    varas_por_comarca,
    visualizar_processo,
)
from .views_movimentacao import (
    movimentar_processo,
    editar_movimentacao,
)

app_name = "processos"

urlpatterns = [
    path("cadastrar/", cadastrar_processo, name="cadastrar_processo"),
    path("area-servidor/", pagina_aluno, name="pagina_aluno"),

    # Movimentação — mais específicas antes de <str:numero>/
    path("<str:numero>/movimentar/<int:mov_id>/", editar_movimentacao, name="editar_movimentacao"),
    path("<str:numero>/movimentar/", movimentar_processo, name="movimentar_processo"),

    path("<str:numero>/", visualizar_processo, name="visualizar_processo"),

    path("api/varas/<int:comarca_id>/", varas_por_comarca, name="varas_por_comarca"),
    path("api/partes/buscar/", buscar_partes, name="buscar_partes"),
    path("api/partes/criar/", criar_parte, name="criar_parte"),
    path("api/atribuir-grupo/", atribuir_grupo_processos, name="atribuir_grupo_processos"),
]
