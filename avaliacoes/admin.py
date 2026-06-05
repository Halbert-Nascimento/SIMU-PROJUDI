from django.contrib import admin

from .models import FeedbackProfessor


@admin.register(FeedbackProfessor)
class FeedbackProfessorAdmin(admin.ModelAdmin):
    list_display = ["id", "professor", "movimentacao", "nota", "data_feedback"]
    list_filter = ["data_feedback", "nota"]
    search_fields = [
        "professor__username",
        "professor__first_name",
        "professor__last_name",
        "comentario",
    ]
    raw_id_fields = ["movimentacao", "professor"]
