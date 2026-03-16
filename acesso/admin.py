from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "tipo_perfil_global", "is_staff", "is_active")
    list_filter = ("tipo_perfil_global", "is_staff", "is_active")
    search_fields = ("username", "email")

    fieldsets = UserAdmin.fieldsets + (
        ("Projudi Acadêmico", {"fields": ("tipo_perfil_global",)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Projudi Acadêmico", {"fields": ("tipo_perfil_global", "email")}),
    )