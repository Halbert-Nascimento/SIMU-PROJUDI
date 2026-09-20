from __future__ import annotations

from django import forms

from .estrelas import (
    ESTRELAS_MAX,
    ESTRELAS_MIN,
    estrelas_para_nota,
    nota_para_estrelas,
    nota_valida,
)
from .models import FeedbackProfessor
from .permissions import pode_avaliar_movimentacao


class FeedbackForm(forms.ModelForm):
    # A nota deixou de ser digitada: o professor escolhe estrelas. Fica fora de
    # `Meta.fields` de propósito — o model não muda, e `clean()` traduz as
    # estrelas para a escala interna da coluna `nota`.
    estrelas = forms.TypedChoiceField(
        label="Avaliação",
        choices=[(str(n), str(n)) for n in range(ESTRELAS_MIN, ESTRELAS_MAX + 1)],
        coerce=int,
        empty_value=None,
        required=False,
        error_messages={
            "invalid_choice": f"Escolha de {ESTRELAS_MIN} a {ESTRELAS_MAX} estrelas.",
        },
    )

    class Meta:
        model = FeedbackProfessor
        fields = ["comentario"]
        widgets = {
            "comentario": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Escreva seu comentário sobre a movimentação...",
            }),
        }

    def __init__(self, *args, ator=None, movimentacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ator = ator
        self.movimentacao = movimentacao
        if self.instance.pk and self.instance.nota is not None:
            self.initial["estrelas"] = nota_para_estrelas(self.instance.nota)

    def clean(self):
        cleaned_data = super().clean()
        if self.ator and self.movimentacao:
            if not pode_avaliar_movimentacao(self.ator, self.movimentacao):
                raise forms.ValidationError(
                    "Você não tem permissão para avaliar esta movimentação."
                )
        nota = self._nota_a_gravar(cleaned_data.get("estrelas"))
        cleaned_data["nota"] = nota
        # `nota` não é campo do form: sem isto o model validaria a nota antiga
        self.instance.nota = nota
        return cleaned_data

    def _nota_a_gravar(self, estrelas):
        atual = self.instance.nota
        if atual is not None and not nota_valida(atual):
            atual = None
        # sem a chave (página antiga, cliente sem navegador) a nota não é apagada
        if self.add_prefix("estrelas") not in self.data:
            return atual
        if estrelas is None:
            return None
        # estrela inalterada mantém a nota antiga: 7,35 não vira 8,00 ao reabrir
        if atual is not None and nota_para_estrelas(atual) == estrelas:
            return atual
        return estrelas_para_nota(estrelas)
