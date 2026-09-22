from django.contrib.auth.models import AbstractUser
from django.db import models

# Versão vigente dos Termos de Uso / Política de Privacidade. Mudar o texto
# desses documentos sem também mudar esta constante (no mesmo commit) deixa o
# aceite antigo registrado como se ainda valesse para o texto novo; mudar só a
# constante sem mudar o texto força um re-aceite vazio, sem motivo.
VERSAO_TERMOS_ATUAL = "1.0"
DATA_VIGENCIA_TERMOS = "2026-09-22"


class Usuario(AbstractUser):
	class TipoPerfilGlobal(models.TextChoices):
		ADMIN = "Admin", "Admin"
		COORDENADOR = "Coordenador", "Coordenador"
		PROFESSOR = "Professor", "Professor"
		ALUNO = "Aluno", "Aluno"
		PENDENTE = "Pendente", "Pendente"

	email = models.EmailField("email", blank=False, unique=True)
	is_coordenador = models.BooleanField("coordenador", default=False)

	tipo_perfil_global = models.CharField(
		max_length=20,
		choices=TipoPerfilGlobal.choices,
		default=TipoPerfilGlobal.PENDENTE,
	)

	aceitou_termos_em = models.DateTimeField("aceitou os termos em", null=True, blank=True)
	versao_termos_aceita = models.CharField(
		"versão dos termos aceita", max_length=20, blank=True, default=""
	)

	class Meta:
		db_table = "usuario"
		verbose_name = "Usuário"
		verbose_name_plural = "Usuários"
