from django.conf import settings
from django.db import models


class StatusCiclo(models.Model):
    nome_status = models.CharField(max_length=45)

    class Meta:
        db_table = "status_ciclo"
        verbose_name = "Status do Ciclo"
        verbose_name_plural = "Status dos Ciclos"

    def __str__(self):
        return self.nome_status


class CicloSimulacao(models.Model):
    nome_edicao = models.CharField(max_length=150)
    coordenador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ciclos_coordenados",
    )
    semestre_ano = models.CharField(max_length=15)
    status = models.ForeignKey(
        StatusCiclo,
        on_delete=models.PROTECT,
        related_name="ciclos",
        db_column="id_status_ciclo",
    )
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="ciclos_participados",
        blank=True,
        db_table="participante_ciclo",
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ciclo_simulacao"
        verbose_name = "Ciclo de Simulação"
        verbose_name_plural = "Ciclos de Simulação"

    def __str__(self):
        return f"{self.nome_edicao} ({self.semestre_ano})"


class GrupoTrabalho(models.Model):
    ciclo = models.ForeignKey(
        CicloSimulacao,
        on_delete=models.CASCADE,
        related_name="grupos",
    )
    nome = models.CharField(max_length=150)
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="grupos_trabalho",
        blank=True,
        db_table="membro_grupo",
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "grupo_trabalho"
        verbose_name = "Grupo de Trabalho"
        verbose_name_plural = "Grupos de Trabalho"

    def __str__(self):
        return f"{self.nome} — {self.ciclo}"
