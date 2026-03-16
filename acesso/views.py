from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import CadastroPublicoForm, LoginForm


# class EntrarView(LoginView):
#     template_name = "acesso/login.html"
#     authentication_form = LoginForm


# class SairView(LogoutView):
#     next_page = reverse_lazy("acesso:login")


def cadastrar(request):
    if request.method == "POST":
        form = CadastroPublicoForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("core:home")
    else:
        form = CadastroPublicoForm()

    return render(request, "acesso/cadastro_usuario.html", {"form": form})