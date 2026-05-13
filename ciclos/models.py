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


class CargoSimulacao(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Cargo Simulação")
    cod = models.CharField(max_length=20, unique=True, verbose_name="Código do Cargo")

    #        nome                   |  Códigos:
    # ('Serventia/Cartório',        | 'SC'),
    # ('Advogados Polo Ativo',      | 'APA'),
    # ('Advogados Polo Passivo',    | 'APP'),
    # ('Ministério Público',        | 'MP'),
    # ('Juiz',                      | 'JZ')


    class Meta:
        db_table = "cargo_simulacao"
        verbose_name = "Cargo de Simulação"
        verbose_name_plural = "Cargos de Simulação"

    def __str__(self):
        return self.nome


class CicloSimulacao(models.Model):
    nome_edicao = models.CharField(max_length=150)
    coordenador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ciclos_coordenados",
        db_column="professor_id",
    )
    semestre = models.PositiveSmallIntegerField()
    ano = models.PositiveSmallIntegerField()
    periodo = models.IntegerField(default=0, blank=True)
    status = models.ForeignKey(
        StatusCiclo,
        on_delete=models.PROTECT,
        related_name="ciclos",
        db_column="status_ciclo_id",
    )
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ParticipanteCiclo",
        related_name="ciclos_participados",
        blank=True,
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ciclo_simulacao"
        verbose_name = "Ciclo de Simulação"
        verbose_name_plural = "Ciclos de Simulação"

    def __str__(self):
        return f"{self.nome_edicao} — {self.semestre}º/{self.ano}"


class ParticipanteCiclo(models.Model):
    ciclo = models.ForeignKey(
        CicloSimulacao,
        on_delete=models.CASCADE,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "participante_ciclo"
        unique_together = [("ciclo", "usuario")]


class GrupoTrabalho(models.Model):
    ciclo = models.ForeignKey(
        CicloSimulacao,
        on_delete=models.CASCADE,
        related_name="grupos",
    )
    cargo_simulacao = models.ForeignKey(
        CargoSimulacao,
        on_delete=models.PROTECT,
        related_name="grupos",
    )
    nome = models.CharField(max_length=150)
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="MembroGrupo",
        related_name="grupos_trabalho",
        blank=True,
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "grupo_trabalho"
        verbose_name = "Grupo de Trabalho"
        verbose_name_plural = "Grupos de Trabalho"

    def __str__(self):
        return f"{self.nome} ({self.cargo_simulacao})"


class MembroGrupo(models.Model):
    grupo = models.ForeignKey(
        GrupoTrabalho,
        on_delete=models.CASCADE,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "membro_grupo"
        unique_together = [("grupo", "usuario")]
