from django.urls import path

from acesso.views import login_view


app_name = "base"

urlpatterns = [
    path("home/", login_view, name="home"),
]
