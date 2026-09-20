from __future__ import annotations

from django import forms

from .models import (
    Comarca,
    ProcessoJudicial,
    VaraServentia,
)
from .services import EstadoInvalidoError, planejar_alteracoes


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


class AtribuicaoGruposForm(forms.Form):
    """
    Um campo por posição processual, montado a partir do estado atual do processo.

    É a única porta de entrada da tela de atribuição: garante que o grupo escolhido é do ciclo
    e de um papel que aquela posição aceita, que nenhum papel ocupa duas posições, e que o
    estado que a tela viu ainda é o do banco. O resultado da validação é o próprio plano, em
    `self.plano` — a view não recalcula nada.
    """

    MANTER = "manter"
    REMOVER = "remover"

    def __init__(self, *args, estados, **kwargs):
        super().__init__(*args, **kwargs)
        self.estados = list(estados)
        self.desejado: dict = {}
        self.plano = None
        self.estado_mudou = False

        for estado in self.estados:
            chave = estado.posicao.chave
            self.fields[f"posicao_{chave}"] = forms.ChoiceField(
                choices=self._escolhas(estado),
                required=True,
                initial=self.MANTER,
                error_messages={
                    "required": f'Escolha qual grupo fica em "{estado.posicao.rotulo}".',
                    "invalid_choice": f'"{estado.posicao.rotulo}" não aceita esse grupo.',
                },
            )
            self.fields[f"atual_{chave}"] = forms.CharField(
                required=False, widget=forms.HiddenInput, initial=estado.impressao,
            )

    def _escolhas(self, estado):
        escolhas = []
        # posição em conflito não oferece "manter": qual grupo fica é justamente o que falta
        # decidir, e tratar o conflito como "deixa como está" apagaria os dois
        if not estado.em_conflito:
            escolhas.append((self.MANTER, "Manter"))
        else:
            escolhas += [(str(grupo.pk), grupo.nome) for grupo in estado.grupos_vinculados]
        escolhas += [(str(grupo.pk), grupo.nome) for grupo in estado.opcoes]
        if estado.grupos_vinculados:
            escolhas.append((self.REMOVER, "Remover"))
        return escolhas

    def clean(self):
        dados = super().clean()
        desejado = {}

        for estado in self.estados:
            chave = estado.posicao.chave
            escolha = dados.get(f"posicao_{chave}")
            if escolha is None:
                continue  # o próprio ChoiceField já acusou

            if (dados.get(f"atual_{chave}") or "").strip() != estado.impressao:
                self.estado_mudou = True
                raise forms.ValidationError(
                    "O processo mudou enquanto esta tela estava aberta. Confira o estado atual "
                    "e refaça as alterações."
                )

            if escolha == self.MANTER:
                continue
            desejado[chave] = None if escolha == self.REMOVER else self._grupo(estado, escolha)

        self.desejado = desejado
        try:
            self.plano = planejar_alteracoes(self.estados, desejado)
        except EstadoInvalidoError as erro:
            raise forms.ValidationError(str(erro))
        return dados

    def _grupo(self, estado, escolha):
        """O ChoiceField já limitou as opções; aqui a escolha volta a ser objeto de domínio."""
        for grupo in tuple(estado.grupos_vinculados) + tuple(estado.opcoes):
            if str(grupo.pk) == escolha:
                return grupo
        raise forms.ValidationError(f'"{estado.posicao.rotulo}" não aceita esse grupo.')
