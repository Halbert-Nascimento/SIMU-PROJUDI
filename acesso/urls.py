from django.urls import path

from .views import  cadastrar



urlpatterns = [
    path("cadastro/", cadastrar, name="cadastro"),
]
