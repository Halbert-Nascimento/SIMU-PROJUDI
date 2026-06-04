from __future__ import annotations

from django.conf import settings
from django.db import models, transaction
from private_storage.fields import PrivateFileField


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
    nome = models.CharField(max_length=150)
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
        FISICA = "Física", "Física"
        JURIDICA = "Jurídica", "Jurídica"

    nome_razao = models.CharField(max_length=150)
    cpf_cnpj = models.CharField(max_length=20, unique=True)
    tipo_pessoa = models.CharField(max_length=8, choices=TipoPessoa.choices)

    class Meta:
        db_table = "parte_ficticia"
        verbose_name = "Parte Fictícia"
        verbose_name_plural = "Partes Fictícias"
        ordering = ["nome_razao"]

    def __str__(self) -> str:
        return f"{self.nome_razao} ({self.cpf_cnpj})"


# ---------------------------------------------------------------------------
# Sequência de numeração CNJ
# ---------------------------------------------------------------------------

class SequenciaNumeroProcesso(models.Model):
    ano = models.PositiveIntegerField()
    tr = models.PositiveSmallIntegerField()
    origem = models.PositiveIntegerField()
    ultimo_seq = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sequencia_numero_processo"
        verbose_name = "Sequência de Número de Processo"
        verbose_name_plural = "Sequências de Número de Processo"
        constraints = [
            models.UniqueConstraint(
                fields=["ano", "tr", "origem"],
                name="uniq_seq_num_proc_chave",
            )
        ]


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
        max_digits=15, decimal_places=2, null=True, blank=True, default="0.00",
    )
    segredo_justica = models.BooleanField(default=False)
    data_autuacao = models.DateTimeField(auto_now_add=True)

    grupos = models.ManyToManyField(
        "ciclos.GrupoTrabalho",
        through="GrupoProcesso",
        related_name="processos",
        blank=True,
    )

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

    @staticmethod
    def _calcular_dv_cnj(numero_base: str) -> str:
        dv = 98 - (int(numero_base) % 97)
        return f"{dv:02d}"

    @classmethod
    def gerar_numero_cnj(cls, *, ano: int, tr: int, origem: int) -> str:
        j = 8  # segmento: Justiça Estadual
        with transaction.atomic():
            sequencia, _ = SequenciaNumeroProcesso.objects.select_for_update().get_or_create(
                ano=ano,
                tr=tr,
                origem=origem,
                defaults={"ultimo_seq": 0},
            )
            sequencia.ultimo_seq += 1
            sequencia.save(update_fields=["ultimo_seq"])
            seq = sequencia.ultimo_seq
        base = f"{seq:07d}{ano:04d}{j}{tr:02d}{origem:04d}00"
        dv = cls._calcular_dv_cnj(base)
        return f"{seq:07d}-{dv}.{ano:04d}.{j}.{tr:02d}.{origem:04d}"

    @property
    def partes_resumo(self):
        polos = self.polos.all()
        ativos = [p.parte.nome_razao for p in polos if p.tipo_polo == "Ativo"]
        passivos = [p.parte.nome_razao for p in polos if p.tipo_polo == "Passivo"]
        ativo_str = ", ".join(ativos) if ativos else "—"
        passivo_str = ", ".join(passivos) if passivos else "—"
        return f"{ativo_str} × {passivo_str}"

    def __str__(self) -> str:
        return self.numero


class GrupoProcesso(models.Model):
    processo = models.ForeignKey(
        ProcessoJudicial,
        on_delete=models.CASCADE,
    )
    grupo = models.ForeignKey(
        "ciclos.GrupoTrabalho",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "grupo_processo"


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
    data_hora = models.DateTimeField()
    link_sala_virtual = models.CharField(max_length=255, null=True, blank=True)
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
        ATIVO = "Ativo", "Ativo"
        PASSIVO = "Passivo", "Passivo"
        TERCEIRO = "Terceiro", "Terceiro"

    processo = models.ForeignKey(
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


# ---------------------------------------------------------------------------
# Movimentação processual
# ---------------------------------------------------------------------------

class TipoMovimentacao(models.Model):
    nome_movimentacao = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_movimentacao"
        verbose_name = "Tipo de Movimentação"
        verbose_name_plural = "Tipos de Movimentação"

    def __str__(self) -> str:
        return self.nome_movimentacao


class MovimentacaoProcessual(models.Model):
    descricao_evento = models.TextField()
    data_movimento = models.DateTimeField(auto_now_add=True)
    processo = models.ForeignKey(
        ProcessoJudicial,
        on_delete=models.CASCADE,
        related_name="movimentacoes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    tipo_movimento = models.ForeignKey(
        TipoMovimentacao,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    movimentacao_origem = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_derivadas",
    )
    antecedente_logico = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consequentes",
    )

    class Meta:
        db_table = "movimentacao_processual"
        verbose_name = "Movimentação Processual"
        verbose_name_plural = "Movimentações Processuais"
        ordering = ["-data_movimento"]

    def __str__(self) -> str:
        return f"{self.tipo_movimento} — {self.processo}"


# ---------------------------------------------------------------------------
# Documento anexado (vinculado a uma movimentação)
# ---------------------------------------------------------------------------

def _upload_to_documento(instance, filename):
    """Gera o caminho: processos/{numero_processo}/{nome_arquivo}"""
    numero = instance.movimentacao.processo.numero
    return f"processos/{numero}/{filename}"


class DocumentoAnexado(models.Model):
    titulo_arquivo = models.CharField(max_length=150)
    caminho_arquivo = PrivateFileField(
        upload_to=_upload_to_documento,
        max_length=255,
    )
    data_upload = models.DateTimeField(auto_now_add=True)
    movimentacao = models.ForeignKey(
        MovimentacaoProcessual,
        on_delete=models.CASCADE,
        related_name="documentos",
    )

    class Meta:
        db_table = "documento_anexado"
        verbose_name = "Documento Anexado"
        verbose_name_plural = "Documentos Anexados"

    def __str__(self) -> str:
        return f"{self.titulo_arquivo} — {self.movimentacao}"
