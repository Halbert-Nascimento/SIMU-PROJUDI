import re

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario

_NAME_REGEX = re.compile(
    r'^[^\W\d_]+'              # começa com uma ou mais letras Unicode (sem dígitos, sem _)
    r"(?:[ '\-][^\W\d_]+)*$",  # seguido opcionalmente de espaço/hífen/apóstrofo + mais letras
    re.UNICODE,
)

_EMAIL_REGEX = re.compile(
    r'^(?![0-9]+@)'                              # parte local não pode ser puramente numérica
    r'(?!.*\.\.)'                                # proíbe pontos consecutivos
    r'[a-z0-9]'                                  # deve começar com alfanumérico
    r'[a-z0-9._-]*'                              # chars permitidos na parte local
    r'(?<![._\-])'                               # não pode terminar com . _ -
    r'@'
    r'[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?'        # domínio principal
    r'(?:\.[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?)*' # subdomínios opcionais
    r'\.[a-z]{2,}$'                              # TLD obrigatório (mínimo 2 letras)
)


class CadastroPublicoForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("first_name", "email", "password1", "password2")
        labels = {"first_name": "Nome Completo"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "w-full border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:border-tjgo-blue focus:ring-1 focus:ring-tjgo-blue",
                    "placeholder": field.label,
                }
            )

    def clean_first_name(self):
        name = self.cleaned_data.get("first_name", "").strip()
        if not _NAME_REGEX.match(name):
            raise forms.ValidationError(
                "Nome inválido. Use apenas letras, espaços e hífens."
            )
        return name

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if not _EMAIL_REGEX.match(email):
            raise forms.ValidationError(
                "E-mail inválido. Por favor, insira um endereço de e-mail válido."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.tipo_perfil_global = Usuario.TipoPerfilGlobal.PENDENTE
        user.is_active = False
        user.is_staff = False
        if commit:
            user.save()
        return user
