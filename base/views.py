from django.shortcuts import render
from django.urls import URLPattern, URLResolver, get_resolver




def home(request):
    return render(request, "acesso/login.html")

def cadastro_processo(request):
    return render(request, "base/cadastro_processo.html")


def _collect_routes(urlpatterns, prefix=""):
    routes = []

    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            route = f"{prefix}{pattern.pattern}".lstrip("/")
            name = pattern.name or "-"
            is_clickable = "<" not in route and str(route) != ""

            routes.append(
                {
                    "route": str(route),
                    "name": name,
                    "clickable": is_clickable,
                }
            )
        elif isinstance(pattern, URLResolver):
            nested_prefix = f"{prefix}{pattern.pattern}"
            routes.extend(_collect_routes(pattern.url_patterns, nested_prefix))

    return routes


def redirecionamento_teste_sucesso(request):
    all_routes = _collect_routes(get_resolver().url_patterns)
    all_routes = sorted(all_routes, key=lambda item: item["route"])

    return render(
        request,
        "base/redirecionamento_teste_sucesso.html",
        {"all_routes": all_routes},
    )