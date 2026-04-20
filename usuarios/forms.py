from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.tipo_perfil_global = Usuario.TipoPerfilGlobal.PENDENTE
        user.is_active = False
        user.is_staff = False
        if commit:
            user.save()
        return user
