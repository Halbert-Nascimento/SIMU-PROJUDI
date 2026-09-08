from django.contrib import admin

from .models import Notificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("destinatario", "tipo", "lida", "data_criacao")
    list_filter = ("tipo", "lida")
    search_fields = ("destinatario__username", "destinatario__first_name", "mensagem")
    autocomplete_fields = ("destinatario",)
    readonly_fields = ("data_criacao",)
