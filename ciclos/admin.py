from django.contrib import admin



from .models import CargoSimulacao, CicloSimulacao, StatusCiclo

@admin.register(StatusCiclo)
class StatusCicloAdmin(admin.ModelAdmin):
    list_display = ("nome_status",)
    search_fields = ("nome_status",)

@admin.register(CargoSimulacao)
class CargoSimulacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "cod")
    search_fields = ("nome", "cod")
    



