from django.db import models

from django.contrib.auth.models import AbstractUser



class Usuario(AbstractUser):
    class TipoPerfilGlobal(models.TextChoices):
        ADMIN = "Admin", "Admin"
        COORDENADOR = "Coordenador", "Coordenador"
        PROFESSOR = "Professor", "Professor"
        ALUNO = "Aluno", "Aluno"
        PENDENTE = "Pendente", "Pendente"

    
    email = models.EmailField("email", blank=False, unique=True)

    tipo_perfil_global = models.CharField(
        max_length=20,
        choices=TipoPerfilGlobal.choices,
        default=TipoPerfilGlobal.PENDENTE,  
    )

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"