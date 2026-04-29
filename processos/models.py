import random

from django.db import models


class Comarca(models.Model):
    nome = models.CharField(max_length=100)

    class Meta:
        db_table = "comarca"
        verbose_name = "Comarca"
        verbose_name_plural = "Comarcas"

    def __str__(self):
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

    def __str__(self):
        return self.nome


class TipoProcesso(models.Model):
    nome = models.CharField(max_length=45)

    class Meta:
        db_table = "tipo_processo"
        verbose_name = "Tipo de Processo"
        verbose_name_plural = "Tipos de Processo"

    def __str__(self):
        return self.nome


class ClasseProcessual(models.Model):
    nome = models.CharField(max_length=150)

    class Meta:
        db_table = "classe_processual"
        verbose_name = "Classe Processual"
        verbose_name_plural = "Classes Processuais"

    def __str__(self):
        return self.nome


class StatusProcessoJudicial(models.Model):
    nome_status = models.CharField(max_length=45)

    class Meta:
        db_table = "status_processo_judicial"
        verbose_name = "Status do Processo Judicial"
        verbose_name_plural = "Status dos Processos Judiciais"

    def __str__(self):
        return self.nome_status


class ProcessoJudicial(models.Model):
    numero = models.CharField(max_length=30, unique=True)
    ciclo = models.ForeignKey(
        "ciclos.CicloSimulacao",
        on_delete=models.CASCADE,
        related_name="processos",
    )
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
    valor_causa = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        blank=True,
    )
    segredo_justica = models.BooleanField(default=False)
    status_atual = models.ForeignKey(
        StatusProcessoJudicial,
        on_delete=models.PROTECT,
        related_name="processos",
    )
    data_autuacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "processo_judicial"
        verbose_name = "Processo Judicial"
        verbose_name_plural = "Processos Judiciais"

    @staticmethod
    def gerar_numero_unico():
        while True:
            seq = random.randint(0, 9_999_999)
            dd = random.randint(0, 99)
            ano = random.randint(2020, 2030)
            j = random.randint(1, 9)
            tr = random.randint(1, 99)
            origem = random.randint(1, 9999)
            numero = f"{seq:07d}-{dd:02d}.{ano}.{j}.{tr:02d}.{origem:04d}"
            if not ProcessoJudicial.objects.filter(numero=numero).exists():
                return numero

    def __str__(self):
        return self.numero


class ParteFicticia(models.Model):
    nome_razao = models.CharField(max_length=150)
    cpf_cnpj = models.CharField(max_length=20, unique=True)
    tipo_pessoa = models.CharField(
        max_length=10,
        choices=[("Física", "Física"), ("Jurídica", "Jurídica")],
    )

    class Meta:
        db_table = "parte_ficticia"
        verbose_name = "Parte Fictícia"
        verbose_name_plural = "Partes Fictícias"

    def __str__(self):
        return self.nome_razao


class PoloProcessual(models.Model):
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
    tipo_polo = models.CharField(
        max_length=10,
        choices=[("Ativo", "Ativo"), ("Passivo", "Passivo"), ("Terceiro", "Terceiro")],
    )

    class Meta:
        db_table = "polo_processual"
        verbose_name = "Polo Processual"
        verbose_name_plural = "Polos Processuais"

    def __str__(self):
        return f"{self.parte} — {self.tipo_polo}"
