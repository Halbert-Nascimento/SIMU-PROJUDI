from django.contrib import admin

from .models import (
    EfeitoColateralMovimentacao,
    PapelAutorizadoMovimentacao,
    PreCondicaoMovimentacao,
    TipoMovimentacao,
)


class PapelAutorizadoMovimentacaoInline(admin.TabularInline):
    model = PapelAutorizadoMovimentacao
    extra = 0


class PreCondicaoMovimentacaoInline(admin.TabularInline):
    model = PreCondicaoMovimentacao
    fk_name = "tipo_movimentacao"
    extra = 0


class EfeitoColateralMovimentacaoInline(admin.TabularInline):
    model = EfeitoColateralMovimentacao
    extra = 0


@admin.register(TipoMovimentacao)
class TipoMovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("nome_movimentacao", "efeito_status")
    list_select_related = ("efeito_status",)
    search_fields = ("nome_movimentacao",)
    ordering = ("nome_movimentacao",)
    inlines = [
        PapelAutorizadoMovimentacaoInline,
        PreCondicaoMovimentacaoInline,
        EfeitoColateralMovimentacaoInline,
    ]
