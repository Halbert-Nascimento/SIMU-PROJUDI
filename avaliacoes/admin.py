from django.contrib import admin

from .estrelas import nota_para_estrelas
from .models import FeedbackProfessor


@admin.register(FeedbackProfessor)
class FeedbackProfessorAdmin(admin.ModelAdmin):
    list_display = ["id", "professor", "movimentacao", "estrelas", "pontos", "data_feedback"]
    list_filter = ["data_feedback", "nota"]
    search_fields = [
        "professor__username",
        "professor__first_name",
        "professor__last_name",
        "comentario",
    ]
    raw_id_fields = ["movimentacao", "professor"]

    @admin.display(description="Estrelas")
    def estrelas(self, feedback):
        estrelas = nota_para_estrelas(feedback.nota)
        return "—" if estrelas is None else f"{estrelas} de 5"

    # O que a tela mostra em estrelas fica gravado em escala 0–10 (1★ = 2).
    @admin.display(description="Pontos (0–10, interna)", ordering="nota")
    def pontos(self, feedback):
        return feedback.nota
