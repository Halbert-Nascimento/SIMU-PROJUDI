from __future__ import annotations

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from usuarios.models import Usuario

from .permissions import pode_alterar_senha, tipos_que_pode_atribuir
from .services import redefinir_senha

class AtualizarUsuarioForm(forms.Form):
    is_active = forms.BooleanField(label="Ativo", required=False)
    tipo_perfil_global = forms.ChoiceField(label="Tipo de Perfil", choices=[])
    nova_senha = forms.CharField(label="Nova senha", widget=forms.PasswordInput, required=False)
    confirmacao_senha = forms.CharField(label="Confirmação", widget=forms.PasswordInput, required=False)

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

    def clean(self):
        cleaned_data = super().clean()

        # Confere o tipo ATUAL do alvo, não só o de destino — sem isso um Coordenador editava um Admin sem perceber.
        if not pode_alterar_senha(self.ator, self.alvo):
            raise forms.ValidationError("Você não tem permissão para alterar dados deste usuário.")

        nova_senha = cleaned_data.get('nova_senha')
        confirmacao_senha = cleaned_data.get('confirmacao_senha')

        if nova_senha or confirmacao_senha:
            if not nova_senha:
                self.add_error('nova_senha', "Preencha a nova senha, ou deixe os dois campos em branco.")
            elif not confirmacao_senha:
                self.add_error('confirmacao_senha', "Confirme a nova senha, ou deixe os dois campos em branco.")
            elif nova_senha != confirmacao_senha:
                self.add_error('confirmacao_senha', "As senhas não coincidem.")
            else:
                try:
                    validate_password(nova_senha, user=self.alvo)
                except forms.ValidationError as exc:
                    self.add_error('nova_senha', exc)

        return cleaned_data

    def aplicar(self):
        perfil = self.cleaned_data['tipo_perfil_global']
        nova_senha = self.cleaned_data.get('nova_senha')

        # Atômico: são dois UPDATEs na mesma linha, e não pode sobrar um sem o outro se um falhar.
        with transaction.atomic():
            # Senha antes do tipo: mudar o tipo primeiro invalidaria a checagem de redefinir_senha().
            if nova_senha:
                redefinir_senha(ator=self.ator, alvo=self.alvo, nova_senha=nova_senha)

            self.alvo.is_active = self.cleaned_data['is_active']
            self.alvo.tipo_perfil_global = perfil
            self.alvo.is_coordenador = perfil == Usuario.TipoPerfilGlobal.COORDENADOR
            # Admin e Coordenador acessam o /admin/ do Django; os demais, não.
            # AdminSite.has_permission() exige is_staff — inclusive de superusuário —,
            # então zerar is_staff para o perfil Admin o trancaria fora do painel.
            self.alvo.is_staff = perfil in (
                Usuario.TipoPerfilGlobal.ADMIN,
                Usuario.TipoPerfilGlobal.COORDENADOR,
            )
            self.alvo.save(update_fields=['is_active', 'tipo_perfil_global', 'is_coordenador', 'is_staff'])

        return self.alvo
