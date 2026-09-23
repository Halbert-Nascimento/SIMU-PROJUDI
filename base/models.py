from django.db import models


class TabelaDominio(models.Model):
    """
    Base para as tabelas de apoio do sistema (comarca, classe processual,
    tipo de audiência, status...), que só carregam um nome e são usadas para
    popular selects.

    Vale para modelos novos. Os existentes ainda nomeiam o campo de quatro
    formas diferentes (`nome`, `nome_status`, `nome_audiencia`,
    `nome_status_audiencia`); uniformizá-los exige RenameField e ajuste dos
    templates, e ficou fora desta refatoração.
    """

    nome = models.CharField(max_length=150)

    class Meta:
        abstract = True
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
