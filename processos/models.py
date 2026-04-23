from __future__ import annotations

from django.db import models


# ---------------------------------------------------------------------------
# Tabelas de domínio / lookup
# ---------------------------------------------------------------------------

class Comarca(models.Model):
    nome = models.CharField(max_length=100)

    class Meta:
        db_table = "comarca"
        verbose_name = "Comarca"
        verbose_name_plural = "Comarcas"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class VaraServentia(models.Model):
    nome    = models.CharField(max_length=150)
    comarca = models.ForeignKey(
        Comarca,
        on_delete=models.PROTECT,
        related_name="varas",
    )

    class Meta:
        db_table = "vara_serventia"
        verbose_name = "Vara / Serventia"
        verbose_name_plural = "Varas / Serventias"
        ordering = ["comarca__nome", "nome"]

    def __str__(self) -> str:
        return f"{self.nome} — {self.comarca}"


class ClasseProcessual(models.Model):
    nome = models.CharField(max_length=150)

    class Meta:
        db_table = "classe_processual"
        verbose_name = "Classe Processual"
        verbose_name_plural = "Classes Processuais"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class StatusProcessoJudicial(models.Model):
    nome_status = models.CharField(max_length=45)

    class Meta:
        db_table = "status_processo_judicial"
        verbose_name = "Status do Processo"
        verbose_name_plural = "Status dos Processos"

    def __str__(self) -> str:
        return self.nome_status


class TipoProcesso(models.Model):
    nome = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_processo"
        verbose_name = "Tipo de Processo"
        verbose_name_plural = "Tipos de Processo"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class StatusAudiencia(models.Model):
    nome_status_audiencia = models.CharField(max_length=45)

    class Meta:
        db_table = "status_audiencia"
        verbose_name = "Status de Audiência"
        verbose_name_plural = "Status de Audiências"

    def __str__(self) -> str:
        return self.nome_status_audiencia


class TipoAudiencia(models.Model):
    nome_audiencia = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_audiencia"
        verbose_name = "Tipo de Audiência"
        verbose_name_plural = "Tipos de Audiência"
        ordering = ["nome_audiencia"]

    def __str__(self) -> str:
        return self.nome_audiencia


# ---------------------------------------------------------------------------
# Parte fictícia (litigantes simulados)
# ---------------------------------------------------------------------------

class ParteFicticia(models.Model):
    class TipoPessoa(models.TextChoices):
        FISICA   = "Física",   "Física"
        JURIDICA = "Jurídica", "Jurídica"

    nome_razao  = models.CharField(max_length=150)
    cpf_cnpj    = models.CharField(max_length=20, unique=True)
    tipo_pessoa = models.CharField(max_length=8, choices=TipoPessoa.choices)

    class Meta:
        db_table = "parte_ficticia"
        verbose_name = "Parte Fictícia"
        verbose_name_plural = "Partes Fictícias"
        ordering = ["nome_razao"]

    def __str__(self) -> str:
        return f"{self.nome_razao} ({self.cpf_cnpj})"


# ---------------------------------------------------------------------------
# Processo judicial
# ---------------------------------------------------------------------------

class ProcessoJudicial(models.Model):
    numero = models.CharField(max_length=30, unique=True)

    # FK para app ciclos
    ciclo = models.ForeignKey(
        "ciclos.CicloSimulacao",
        on_delete=models.PROTECT,
        related_name="processos",
    )

    # FKs internas ao app processos
    vara = models.ForeignKey(
        VaraServentia,
        on_delete=models.PROTECT,
        related_name="processos",
    )
    tipo_processo = models.ForeignKey(
        TipoProcesso,
        on_delete=models.PROTECT,
        related_name="processos",
    )
    classe = models.ForeignKey(
        ClasseProcessual,
        on_delete=models.PROTECT,
        related_name="processos",
    )
    
    status_atual = models.ForeignKey(
        StatusProcessoJudicial,
        on_delete=models.PROTECT,
        related_name="processos",
        
    )

    valor_causa = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True, default="0.00",
    )
    segredo_justica = models.BooleanField(default=False)
    data_autuacao   = models.DateTimeField(auto_now_add=True)

    # grupo_processo: tabela de ligação pura (sem campos extras)
    # → ManyToManyField nativo; db_table mapeia para a tabela SQL exata
    grupos = models.ManyToManyField(
        "ciclos.GrupoTrabalho",
        related_name="processos",
        blank=True,
        db_table="grupo_processo",
    )

    # polo_processual: tabela de ligação COM campo extra (tipo_polo)
    # → ManyToManyField com through; tabela controlada pelo Meta de PoloProcessual
    partes = models.ManyToManyField(
        ParteFicticia,
        through="PoloProcessual",
        related_name="processos",
        blank=True,
    )

    class Meta:
        db_table = "processo_judicial"
        verbose_name = "Processo Judicial"
        verbose_name_plural = "Processos Judiciais"
        ordering = ["-data_autuacao"]

    def __str__(self) -> str:
        return self.numero


# ---------------------------------------------------------------------------
# Audiência
# ---------------------------------------------------------------------------

class Audiencia(models.Model):
    processo = models.ForeignKey(
        ProcessoJudicial,
        on_delete=models.CASCADE,
        related_name="audiencias",
    )
    tipo_audiencia = models.ForeignKey(
        TipoAudiencia,
        on_delete=models.PROTECT,
        related_name="audiencias",
    )
    status_audiencia = models.ForeignKey(
        StatusAudiencia,
        on_delete=models.PROTECT,
        related_name="audiencias",
    )
    data_hora            = models.DateTimeField()
    link_sala_virtual    = models.CharField(max_length=255, null=True, blank=True)
    data_hora_realizacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audiencia"
        verbose_name = "Audiência"
        verbose_name_plural = "Audiências"
        ordering = ["data_hora"]

    def __str__(self) -> str:
        return f"{self.tipo_audiencia} — {self.processo} ({self.data_hora:%d/%m/%Y %H:%M})"


# ---------------------------------------------------------------------------
# Polo processual (tabela de ligação com campo extra → through model)
# ---------------------------------------------------------------------------

class PoloProcessual(models.Model):
    class TipoPolo(models.TextChoices):
        ATIVO    = "Ativo",    "Ativo"
        PASSIVO  = "Passivo",  "Passivo"
        TERCEIRO = "Terceiro", "Terceiro"

    processo  = models.ForeignKey(
        ProcessoJudicial,
        on_delete=models.CASCADE,
        related_name="polos",
    )
    parte = models.ForeignKey(
        ParteFicticia,
        on_delete=models.PROTECT,
        related_name="polos",
    )
    tipo_polo = models.CharField(max_length=8, choices=TipoPolo.choices)

    class Meta:
        db_table = "polo_processual"
        verbose_name = "Polo Processual"
        verbose_name_plural = "Polos Processuais"
        constraints = [
            models.UniqueConstraint(
                fields=["processo", "parte", "tipo_polo"],
                name="unique_polo_por_processo_e_parte",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_polo_display()} — {self.parte} › {self.processo}"
