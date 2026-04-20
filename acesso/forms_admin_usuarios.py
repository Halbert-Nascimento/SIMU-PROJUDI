from __future__ import annotations

from django import forms
from usuarios.models import Usuario

from .permissions import tipos_que_pode_atribuir

class AtualizarUsuarioForm(forms.Form):
    is_active = forms.BooleanField(label="Ativo", required=False)
    tipo_perfil_global = forms.ChoiceField(label="Tipo de Perfil", choices=[])

    def __init__(self, *args, ator: Usuario, alvo: Usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.ator = ator
        self.alvo = alvo

        tipos_permitidos = tipos_que_pode_atribuir(ator)

        # montar choices apenas com os tipos que o ator pode atribuir
        self.fields['tipo_perfil_global'].choices = [
            (tipo, tipo.label)
            for tipo in tipos_permitidos
        ]

        self.initial['is_active'] = alvo.is_active
        self.initial['tipo_perfil_global'] = alvo.tipo_perfil_global

        # segunda validaçao para garantir que o ator não consiga atribuir um tipo que não tem permissão, mesmo que tente burlar o frontend
        if not self.fields['tipo_perfil_global'].choices:
            self.fields['tipo_perfil_global'].disabled = True

    def clean_tipo_perfil_global(self):
        tipo = self.cleaned_data['tipo_perfil_global']
        permitidos = tipos_que_pode_atribuir(self.ator)
        if tipo not in permitidos:
            raise forms.ValidationError("Você não tem permissão para atribuir esse tipo de perfil.")
        return tipo
    
    def aplicar(self):
        self.alvo.is_active = self.cleaned_data['is_active']
        self.alvo.tipo_perfil_global = self.cleaned_data['tipo_perfil_global']
        if self.alvo.tipo_perfil_global == Usuario.TipoPerfilGlobal.COORDENADOR:
            self.alvo.is_coordenador = True
            self.alvo.is_staff = True # Coordenadores também são staff # NOATA: isso é necessário para acessar o admin, mas pode ser repensado se for criado um painel de administração customizado
        else:
            self.alvo.is_coordenador = False
            self.alvo.is_staff = False
        self.alvo.save(update_fields=['is_active', 'tipo_perfil_global', 'is_coordenador', 'is_staff'])
        return self.alvo