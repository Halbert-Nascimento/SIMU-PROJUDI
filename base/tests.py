from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class PaginasDeErroTests(TestCase):
    """
    DEBUG=False é o que faz o Django procurar 404.html/500.html/etc. em vez
    da tela técnica de debug -- sem isso o teste passaria mesmo se
    TEMPLATES['DIRS'] parasse de apontar para a pasta templates/ da raiz.
    """

    def test_url_inexistente_usa_404_customizado(self):
        response = self.client.get("/esta-url-nao-existe/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_falha_de_csrf_usa_403_csrf_customizado(self):
        # enforce_csrf_checks=True: o client de teste ignora CSRF por padrão.
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("acesso:login"), {"username": "x", "password": "y"})
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403_csrf.html")
