from django.test import TestCase

from usuarios.forms import CadastroPublicoForm
from usuarios.models import VERSAO_TERMOS_ATUAL


def _dados_cadastro(**sobrescritas):
    dados = {
        "first_name": "Maria Souza",
        "email": "maria.souza@teste.local",
        "password1": "senha-forte-123",
        "password2": "senha-forte-123",
    }
    dados.update(sobrescritas)
    return dados


class CadastroPublicoFormAceiteTermosTests(TestCase):
    """Cobre a exigência de aceite dos Termos de Uso / Política de Privacidade
    no autocadastro — usuarios.forms.CadastroPublicoForm.aceite_termos."""

    def test_sem_marcar_aceite_termos_formulario_e_invalido(self):
        form = CadastroPublicoForm(data=_dados_cadastro())

        self.assertFalse(form.is_valid())
        self.assertIn("aceite_termos", form.errors)

    def test_marcando_aceite_termos_cria_usuario_com_aceite_registrado(self):
        form = CadastroPublicoForm(data=_dados_cadastro(aceite_termos="on"))

        self.assertTrue(form.is_valid(), form.errors)
        usuario = form.save()

        self.assertEqual(usuario.versao_termos_aceita, VERSAO_TERMOS_ATUAL)
        self.assertIsNotNone(usuario.aceitou_termos_em)
