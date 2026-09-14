from __future__ import annotations

from django import forms

from .models import (
    Comarca,
    MovimentacaoProcessual,
    ProcessoJudicial,
    TipoMovimentacao,
    VaraServentia,
)


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
        self.fields["valor_causa"].required = True


class MovimentacaoForm(forms.ModelForm):
    """
    Valida a movimentação antes de ela virar INSERT.

    Sem isso `tipo_movimento` ia do `<input type="hidden">` direto para a FK:
    um valor não numérico virava ValueError e um id inexistente virava
    IntegrityError — os dois como 500, com a peça recém-escrita perdida.
    """

    class Meta:
        model = MovimentacaoProcessual
        fields = ["tipo_movimento", "descricao_evento"]
        error_messages = {
            "tipo_movimento": {
                "required": "Selecione o tipo de movimentação.",
                "invalid_choice": "Tipo de movimentação inválido.",
            },
            "descricao_evento": {"required": "Descreva a movimentação."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # mesmo recorte que a tela usa para montar o combobox: "Cadastro do
        # Processo" é gerado no cadastro e não pode ser escolhido aqui
        self.fields["tipo_movimento"].queryset = (
            TipoMovimentacao.objects
            .exclude(nome_movimentacao="Cadastro do Processo")
            .order_by("nome_movimentacao")
        )
        # a tela marca só "Tipo Movimentação" com asterisco, então a descrição
        # segue opcional como é hoje; TextField() sem blank=True a tornaria
        # obrigatória e quebraria movimentações que só anexam documento
        self.fields["descricao_evento"].required = False
