from django.contrib import admin

from .models import (
    Audiencia,
    ClasseProcessual,
    Comarca,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
    StatusAudiencia,
    StatusProcessoJudicial,
    TipoAudiencia,
    TipoProcesso,
    VaraServentia,
)


@admin.register(Comarca)
class ComarcaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(VaraServentia)
class VaraServentiaAdmin(admin.ModelAdmin):
    list_display = ("nome", "comarca")
    list_filter = ("comarca",)
    search_fields = ("nome",)


@admin.register(ClasseProcessual)
class ClasseProcessualAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(StatusProcessoJudicial)
class StatusProcessoJudicialAdmin(admin.ModelAdmin):
    list_display = ("nome_status",)


@admin.register(TipoProcesso)
class TipoProcessoAdmin(admin.ModelAdmin):
    list_display = ("nome",)


@admin.register(StatusAudiencia)
class StatusAudienciaAdmin(admin.ModelAdmin):
    list_display = ("nome_status_audiencia",)


@admin.register(TipoAudiencia)
class TipoAudienciaAdmin(admin.ModelAdmin):
    list_display = ("nome_audiencia",)


@admin.register(ParteFicticia)
class ParteFicticiaAdmin(admin.ModelAdmin):
    list_display = ("nome_razao", "cpf_cnpj", "tipo_pessoa")
    list_filter = ("tipo_pessoa",)
    search_fields = ("nome_razao", "cpf_cnpj")


class AudienciaInline(admin.TabularInline):
    model = Audiencia
    extra = 0
    fields = ("data_hora", "tipo_audiencia", "status_audiencia", "link_sala_virtual")


class PoloProcessualInline(admin.TabularInline):
    model = PoloProcessual
    extra = 0
    fields = ("parte", "tipo_polo")


@admin.register(ProcessoJudicial)
class ProcessoJudicialAdmin(admin.ModelAdmin):
    list_display = ("numero", "ciclo", "vara", "tipo_processo", "status_atual", "data_autuacao")
    list_filter = ("status_atual", "tipo_processo", "vara__comarca")
    search_fields = ("numero",)
    inlines = [PoloProcessualInline, AudienciaInline]
    filter_horizontal = ("grupos",)


@admin.register(Audiencia)
class AudienciaAdmin(admin.ModelAdmin):
    list_display = ("processo", "tipo_audiencia", "status_audiencia", "data_hora")
    list_filter = ("status_audiencia", "tipo_audiencia")
    search_fields = ("processo__numero",)


@admin.register(PoloProcessual)
class PoloProcessualAdmin(admin.ModelAdmin):
    list_display = ("processo", "parte", "tipo_polo")
    list_filter = ("tipo_polo",)
    search_fields = ("processo__numero", "parte__nome_razao")
