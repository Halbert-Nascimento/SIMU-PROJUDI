from django.contrib import admin

from .models import TipoMovimentacao


@admin.register(TipoMovimentacao)
class TipoMovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("nome_movimentacao",)
    search_fields = ("nome_movimentacao",)
    ordering = ("nome_movimentacao",)
