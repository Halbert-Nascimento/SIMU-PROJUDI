from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .services import alterar_minha_senha


class LoginForm(AuthenticationForm):
    pass


class AlterarMinhaSenhaForm(PasswordChangeForm):
    """
    Widgets não levam CLASSE_CAMPO: acesso/templates/acesso/minha_conta.html constrói os
    <input> à mão (para poder envolver cada um num <div class="relative"> próprio, que o
    script de mostrar/ocultar senha de base.html exige) em vez de renderizar {{ field }}.
    """

    def save(self, commit=True):
        # Passa por alterar_minha_senha (log de auditoria) em vez do set_password padrão.
        if not commit:
            raise NotImplementedError(
                "AlterarMinhaSenhaForm.save() sempre persiste via alterar_minha_senha; "
                "commit=False não é suportado."
            )
        alterar_minha_senha(usuario=self.user, nova_senha=self.cleaned_data["new_password1"])
        return self.user
