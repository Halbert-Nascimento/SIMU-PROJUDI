import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from base.ui import CLASSE_CAMPO

from .models import VERSAO_TERMOS_ATUAL, Usuario

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


def campo_aceite_termos(mensagem_erro):
    """Campo do checkbox de aceite dos Termos de Uso / Política de Privacidade.

    Compartilhado por `CadastroPublicoForm` (abaixo) e por
    `acesso.forms.AceiteTermosForm` — é o mesmo campo nos dois lugares, só a
    mensagem de erro muda conforme o contexto (criar conta vs. reaceitar).
    """
    return forms.BooleanField(
        required=True,
        error_messages={"required": mensagem_erro},
    )


class CadastroPublicoForm(UserCreationForm):
    aceite_termos = campo_aceite_termos(
        "É necessário aceitar os Termos de Uso e a Política de "
        "Privacidade para criar a conta."
    )

    class Meta:
        model = Usuario
        fields = ("first_name", "email", "password1", "password2")
        labels = {"first_name": "Nome Completo"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # aceite_termos é renderizado à mão em _aceite_termos_campo.html,
            # não pelo loop genérico de campos — não leva estilo de campo de texto.
            if name == "aceite_termos":
                continue
            field.widget.attrs.update(
                {
                    "class": CLASSE_CAMPO,
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
        user.aceitou_termos_em = timezone.now()
        user.versao_termos_aceita = VERSAO_TERMOS_ATUAL
        if commit:
            user.save()
        return user
