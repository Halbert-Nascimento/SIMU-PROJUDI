from django.shortcuts import render


def gerenciar_grupos(request):
    nome_ciclo = request.GET.get("ciclo", "")
    return render(request, "ciclos/gerenciar_grupos.html", {"nome_ciclo": nome_ciclo})
