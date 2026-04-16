from __future__ import annotations

import datetime

from django import forms

from .models import CargoSimulacao, CicloSimulacao, GrupoTrabalho

_ANO_ATUAL = datetime.date.today().year

SEMESTRE_CHOICES = [
    ("", "Selecione..."),
    (1, "1º Semestre"),
    (2, "2º Semestre"),
]


class CicloSimulacaoForm(forms.ModelForm):
    semestre = forms.ChoiceField(
        choices=SEMESTRE_CHOICES,
        error_messages={"required": "Informe o semestre."},
    )

    class Meta:
        model = CicloSimulacao
        fields = ["nome_edicao", "semestre", "ano", "periodo", "status"]
        error_messages = {
            "nome_edicao": {"required": "O nome da edição é obrigatório."},
            "ano": {"required": "Informe o ano."},
            "status": {"required": "Selecione um status."},
        }

    def clean_nome_edicao(self):
        nome = self.cleaned_data["nome_edicao"].strip()
        if CicloSimulacao.objects.filter(nome_edicao__iexact=nome).exists():
            raise forms.ValidationError(
                f'Já existe um ciclo com o nome "{nome}".'
            )
        return nome

    def clean_semestre(self):
        value = self.cleaned_data["semestre"]
        if not value:
            raise forms.ValidationError("Informe o semestre.")
        return int(value)

    def clean_ano(self):
        ano = self.cleaned_data["ano"]
        if ano < 2000 or ano > _ANO_ATUAL + 5:
            raise forms.ValidationError(
                f"Ano inválido. Informe um valor entre 2000 e {_ANO_ATUAL + 5}."
            )
        return ano


class GrupoTrabalhoForm(forms.ModelForm):
    class Meta:
        model = GrupoTrabalho
        fields = ["nome", "cargo_simulacao"]
        error_messages = {
            "nome": {"required": "O nome do grupo é obrigatório."},
            "cargo_simulacao": {"required": "Selecione o papel na simulação."},
        }

    def __init__(self, *args, ciclo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ciclo = ciclo
        self.fields["cargo_simulacao"].queryset = CargoSimulacao.objects.all()
        self.fields["cargo_simulacao"].empty_label = "Selecione o papel..."

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        qs = GrupoTrabalho.objects.filter(nome__iexact=nome, ciclo=self.ciclo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'Já existe um grupo com o nome "{nome}" neste ciclo.'
            )
        return nome
