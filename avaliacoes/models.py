from __future__ import annotations

from django.conf import settings
from django.db import models


class FeedbackProfessor(models.Model):
    movimentacao = models.ForeignKey(
        "processos.MovimentacaoProcessual",
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="feedbacks_dados",
    )
    comentario = models.TextField()
    nota = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
    )
    data_feedback = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feedback_professor"
        verbose_name = "Feedback do Professor"
        verbose_name_plural = "Feedbacks dos Professores"
        ordering = ["-data_feedback"]

    def __str__(self) -> str:
        return f"Feedback #{self.pk} — {self.movimentacao}"
