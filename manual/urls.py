from django.conf import settings
from django.urls import path
from django.views.static import serve

from .views import capitulo, indice

app_name = "manual"

# Rota própria, e não STATICFILES_DIRS com prefixo: no Windows o finder do Django não
# casa prefixo com "/" e as capturas dariam 404 no ambiente de desenvolvimento.
CAPTURAS = settings.BASE_DIR / "manual-usuario" / "assets"

urlpatterns = [
    path("", indice, name="indice"),
    path("img/<path:path>", serve, {"document_root": CAPTURAS}, name="imagem"),
    path("<slug:slug>/", capitulo, name="capitulo"),
]
