from __future__ import annotations

from django.conf import settings
from django.db import models
from private_storage.fields import PrivateFileField


class TipoMovimentacao(models.Model):
    nome_movimentacao = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_movimentacao"
        verbose_name = "Tipo de Movimentação"
        verbose_name_plural = "Tipos de Movimentação"

    def __str__(self) -> str:
        return self.nome_movimentacao


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


# ---------------------------------------------------------------------------
# Documento anexado (vinculado a uma movimentação)
# ---------------------------------------------------------------------------

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
