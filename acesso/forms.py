from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario


class LoginForm(AuthenticationForm):
    pass


class CadastroPublicoForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("first_name", "email", "password1", "password2")

        labels = {"first_name": "Nome Completo",}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:border-tjgo-blue focus:ring-1 focus:ring-tjgo-blue',
                'placeholder': field.label,
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Use o email como username
        # user.first_name = user.email.split('@')[0]  # Define o nome de usuário como a parte antes do @

        # Registro público: defina o tipo como pendente
        user.tipo_perfil_global = Usuario.TipoPerfilGlobal.PENDENTE
        user.is_active = False  # Desativa a conta até que seja aprovada por um administrador
        if commit:
            user.save()
        return user