from __future__ import annotations

from django.conf import settings
from django.db import models


class TipoNotificacao(models.TextChoices):
    CICLO_STATUS_ALTERADO = "ciclo_status_alterado", "Mudança de status do ciclo"
    MOVIMENTACAO_REGISTRADA = "movimentacao_registrada", "Nova movimentação processual"
    GRUPO_VINCULADO_PROCESSO = "grupo_vinculado_processo", "Grupo vinculado a um processo"
    CICLO_COORDENADOR_ATRIBUIDO = "ciclo_coordenador_atribuido", "Coordenador designado"
    CICLO_PARTICIPANTE_ADICIONADO = "ciclo_participante_adicionado", "Adicionado a um ciclo"


NOTIFICACOES_RECENTES_LIMIT = 10


class Notificacao(models.Model):
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    tipo = models.CharField(max_length=50, choices=TipoNotificacao.choices)
    mensagem = models.CharField(max_length=255)
    link_url = models.CharField(max_length=255, blank=True)
    lida = models.BooleanField(default=False)
    data_leitura = models.DateTimeField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificacao"
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ["-data_criacao"]
        indexes = [
            models.Index(fields=["destinatario", "lida"], name="idx_notif_destinatario_lida"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.destinatario}"
