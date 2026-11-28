from __future__ import annotations

import re

from django import forms

from .models import (
    Comarca,
    ParteFicticia,
    ProcessoJudicial,
    VaraServentia,
)

# só o formato: os seeds usam números sem dígito verificador; o CNPJ aceita letras
_FORMATOS_DOCUMENTO = {
    ParteFicticia.TipoPessoa.FISICA: re.compile(
        r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}", re.ASCII
    ),
    ParteFicticia.TipoPessoa.JURIDICA: re.compile(
        r"[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-\d{2}|[0-9A-Z]{12}\d{2}",
        re.ASCII | re.IGNORECASE,
    ),
}
_ERRO_FORMATO = {
    ParteFicticia.TipoPessoa.FISICA: (
        "CPF inválido. Use 000.000.000-00 ou os 11 dígitos."
    ),
    ParteFicticia.TipoPessoa.JURIDICA: (
        "CNPJ inválido. Use 00.000.000/0000-00 ou os 14 caracteres."
    ),
}
_PREENCHA_TUDO = "Preencha todos os campos."


class _TextoEstritoField(forms.CharField):
    """CharField converteria número ou objeto do JSON em texto e gravaria."""

    def to_python(self, value):
        if value is not None:
            try:
                # surrogate solto é str válida no Python e erro ao gravar no banco
                value.encode("utf-8")
            except (AttributeError, UnicodeEncodeError):
                raise forms.ValidationError("Valor inválido.", code="tipo") from None
        return super().to_python(value)


class _EscolhaSemEspacosField(forms.ChoiceField):
    def to_python(self, value):
        return super().to_python(value).strip()


class ParteFicticiaForm(forms.Form):
    nome_razao = _TextoEstritoField(
        max_length=150,
        error_messages={"max_length": "O nome deve ter no máximo 150 caracteres."},
    )
    cpf_cnpj = _TextoEstritoField(
        max_length=20,
        error_messages={"max_length": "O CPF/CNPJ deve ter no máximo 20 caracteres."},
    )
    tipo_pessoa = _EscolhaSemEspacosField(
        choices=ParteFicticia.TipoPessoa.choices,
        error_messages={"invalid_choice": "Tipo de pessoa inválido."},
    )

    def __init__(self, *args, parte_atual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parte_atual = parte_atual

    def clean(self):
        dados = super().clean()
        documento = dados.get("cpf_cnpj")
        tipo = dados.get("tipo_pessoa")
        if not documento or not tipo:
            return dados

        # cadastro antigo fora do formato continua permitindo corrigir o nome
        atual = self.parte_atual
        # strip: o valor enviado já chega sem espaços; o gravado por carga pode tê-los
        if atual and (documento, tipo) == (atual.cpf_cnpj.strip(), atual.tipo_pessoa):
            return dados

        if not _FORMATOS_DOCUMENTO[tipo].fullmatch(documento):
            if any(f.fullmatch(documento) for f in _FORMATOS_DOCUMENTO.values()):
                raise forms.ValidationError(
                    "O documento informado não corresponde ao tipo de pessoa."
                )
            raise forms.ValidationError(_ERRO_FORMATO[tipo])
        # CNPJ alfanumérico é oficialmente maiúsculo
        dados["cpf_cnpj"] = documento.upper()
        return dados

    def mensagem_de_erro(self) -> str:
        """Uma mensagem só, como a tela espera no campo "erro" do JSON."""
        if any(
            erro.code == "required"
            for erros in self.errors.as_data().values()
            for erro in erros
        ):
            return _PREENCHA_TUDO
        ordem = [*self.fields, forms.forms.NON_FIELD_ERRORS]
        return next(self.errors[campo][0] for campo in ordem if campo in self.errors)


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
