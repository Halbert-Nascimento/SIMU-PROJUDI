from __future__ import annotations

from decimal import Decimal

from django import forms

from .models import FeedbackProfessor
from .permissions import pode_avaliar_movimentacao


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackProfessor
        fields = ["comentario", "nota"]
        widgets = {
            "comentario": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Escreva seu comentário sobre a movimentação...",
            }),
            "nota": forms.NumberInput(attrs={
                "min": "0",
                "max": "10",
                "step": "0.01",
                "placeholder": "0.00",
            }),
        }

    def __init__(self, *args, ator=None, movimentacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ator = ator
        self.movimentacao = movimentacao

    def clean_nota(self):
        nota = self.cleaned_data.get("nota")
        if nota is not None:
            if nota < Decimal("0"):
                raise forms.ValidationError("A nota não pode ser negativa.")
            if nota > Decimal("10"):
                raise forms.ValidationError("A nota não pode ser maior que 10.")
        return nota

    def clean(self):
        cleaned_data = super().clean()
        if self.ator and self.movimentacao:
            if not pode_avaliar_movimentacao(self.ator, self.movimentacao):
                raise forms.ValidationError(
                    "Você não tem permissão para avaliar esta movimentação."
                )
        return cleaned_data
