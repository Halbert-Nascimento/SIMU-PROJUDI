from __future__ import annotations

from django.conf import settings
from django.db import models
from private_storage.fields import PrivateFileField


class CategoriaEfeitoColateral(models.TextChoices):
    ABRE_PRAZO = "abre_prazo", "Abre prazo"
    ENCERRA_PRAZO = "encerra_prazo", "Encerra prazo"
    REABRE_PRAZO = "reabre_prazo", "Reabre prazo"
    AGENDA_AUDIENCIA = "agenda_audiencia", "Agenda audiência"
    NOTIFICA = "notifica", "Notifica"


class TipoMovimentacao(models.Model):
    nome_movimentacao = models.CharField(max_length=45)

    papeis_autorizados = models.ManyToManyField(
        "ciclos.CargoSimulacao",
        through="PapelAutorizadoMovimentacao",
        related_name="tipos_movimentacao",
        blank=True,
    )
    precondicoes = models.ManyToManyField(
        "self",
        through="PreCondicaoMovimentacao",
        through_fields=("tipo_movimentacao", "precondicao"),
        symmetrical=False,
        related_name="habilita_estes",
        blank=True,
    )
    efeito_status = models.ForeignKey(
        "processos.StatusProcessoJudicial",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tipos_movimentacao",
    )

    class Meta:
        db_table = "tipo_movimentacao"
        verbose_name = "Tipo de Movimentação"
        verbose_name_plural = "Tipos de Movimentação"

    def __str__(self) -> str:
        return self.nome_movimentacao


class PapelAutorizadoMovimentacao(models.Model):
    tipo_movimentacao = models.ForeignKey(TipoMovimentacao, on_delete=models.CASCADE)
    cargo_simulacao = models.ForeignKey("ciclos.CargoSimulacao", on_delete=models.CASCADE)

    class Meta:
        db_table = "papel_autorizado_movimentacao"
        unique_together = [("tipo_movimentacao", "cargo_simulacao")]


class PreCondicaoMovimentacao(models.Model):
    tipo_movimentacao = models.ForeignKey(
        TipoMovimentacao,
        on_delete=models.CASCADE,
        related_name="+",
    )
    precondicao = models.ForeignKey(
        TipoMovimentacao,
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        db_table = "precondicao_movimentacao"
        unique_together = [("tipo_movimentacao", "precondicao")]


class EfeitoColateralMovimentacao(models.Model):
    tipo_movimentacao = models.ForeignKey(
        TipoMovimentacao,
        on_delete=models.CASCADE,
        related_name="efeitos_colaterais",
    )
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaEfeitoColateral.choices,
    )

    class Meta:
        db_table = "efeito_colateral_movimentacao"
        verbose_name = "Efeito Colateral de Movimentação"
        verbose_name_plural = "Efeitos Colaterais de Movimentação"
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_movimentacao", "categoria"],
                name="uniq_efeito_colateral_tipo_categoria",
            )
        ]

    def __str__(self) -> str:
        return f"{self.tipo_movimentacao} — {self.get_categoria_display()}"


class MovimentacaoProcessual(models.Model):
    descricao_evento = models.TextField()
    data_movimento = models.DateTimeField(auto_now_add=True)
    processo = models.ForeignKey(
        "processos.ProcessoJudicial",
        on_delete=models.CASCADE,
        related_name="movimentacoes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    tipo_movimento = models.ForeignKey(
        TipoMovimentacao,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    grupo_processo = models.ForeignKey(
        "processos.GrupoProcesso",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes",
    )
    movimentacao_origem = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_derivadas",
    )
    antecedente_logico = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consequentes",
    )

    class Meta:
        db_table = "movimentacao_processual"
        verbose_name = "Movimentação Processual"
        verbose_name_plural = "Movimentações Processuais"
        ordering = ["-data_movimento"]

    def __str__(self) -> str:
        return f"{self.tipo_movimento} — {self.processo}"


def _upload_to_documento(instance, filename):
    """Gera o caminho: processos/{numero_processo}/{nome_arquivo}"""
    numero = instance.movimentacao.processo.numero
    return f"processos/{numero}/{filename}"


class DocumentoAnexado(models.Model):
    titulo_arquivo = models.CharField(max_length=150)
    caminho_arquivo = PrivateFileField(
        upload_to=_upload_to_documento,
        max_length=255,
    )
    data_upload = models.DateTimeField(auto_now_add=True)
    movimentacao = models.ForeignKey(
        MovimentacaoProcessual,
        on_delete=models.CASCADE,
        related_name="documentos",
    )

    class Meta:
        db_table = "documento_anexado"
        verbose_name = "Documento Anexado"
        verbose_name_plural = "Documentos Anexados"

    def __str__(self) -> str:
        return f"{self.titulo_arquivo} — {self.movimentacao}"
