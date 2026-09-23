from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .estrelas import NOTA_MAX, NOTA_MIN, nota_valida


class FeedbackProfessor(models.Model):
    movimentacao = models.ForeignKey(
        "movimentacoes.MovimentacaoProcessual",
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
        constraints = [
            # A view já trata o par (movimentação, professor) como único ao
            # reaproveitar o feedback existente. Sem a restrição, um duplo envio
            # do formulário criava dois registros e a nota duplicada entrava duas
            # vezes no Avg()/Count() de `minhas_notas`.
            models.UniqueConstraint(
                fields=["movimentacao", "professor"],
                name="uniq_feedback_por_mov_e_professor",
                violation_error_message="Você já avaliou esta movimentação.",
            ),
        ]

    def __str__(self) -> str:
        return f"Feedback #{self.pk} — {self.movimentacao}"

    # clean() não gera migration: o admin recusa nota fora de 0–10 sem constraint
    def clean(self):
        if self.nota is not None and not nota_valida(self.nota):
            raise ValidationError(
                {"nota": f"A nota deve estar entre {NOTA_MIN} e {NOTA_MAX}."}
            )
