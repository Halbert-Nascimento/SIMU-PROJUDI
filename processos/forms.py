from __future__ import annotations

from django import forms

from .models import Comarca, ProcessoJudicial, VaraServentia


class ProcessoJudicialForm(forms.ModelForm):
    comarca = forms.ModelChoiceField(
        queryset=Comarca.objects.all().order_by("nome"),
        empty_label="Selecione a comarca...",
        required=True,
        error_messages={"required": "Selecione uma comarca."},
    )

    class Meta:
        model = ProcessoJudicial
        fields = [
            "vara",
            "tipo_processo",
            "classe",
            "valor_causa",
            "segredo_justica",
        ]
        widgets = {
            "tipo_processo": forms.RadioSelect,
        }
        error_messages = {
            "vara": {"required": "Selecione uma vara."},
            "tipo_processo": {"required": "Selecione o tipo do processo."},
            "classe": {"required": "Selecione a classe processual."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["vara"].queryset = VaraServentia.objects.none()
        self.fields["vara"].empty_label = "Selecione a vara..."

        if self.data.get("comarca"):
            try:
                comarca_id = int(self.data.get("comarca"))
                self.fields["vara"].queryset = VaraServentia.objects.filter(
                    comarca_id=comarca_id
                )
            except (ValueError, TypeError):
                pass

        self.fields["tipo_processo"].empty_label = None
        self.fields["classe"].empty_label = "Selecione a classe..."
        self.fields["classe"].queryset = self.fields["classe"].queryset.order_by("nome")
        self.fields["valor_causa"].required = False
