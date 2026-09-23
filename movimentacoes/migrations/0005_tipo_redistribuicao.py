# Acrescenta "Redistribuição" ao catálogo. Fica fora do CATALOGO sequencial da 0004 por
# duas razões: é transversal (repete a cada troca de grupo, sem pré-condição e sem efeito
# sobre o status) e não tem papel autorizado — quem a registra é a tela de atribuição de
# grupos, nunca o formulário de movimentar. Sem papel, `tipos_praticaveis` não a oferece e
# `pode_praticar_movimentacao` barra POST forjado.

from django.db import migrations

NOME = "Redistribuição"


def criar(apps, schema_editor):
    TipoMovimentacao = apps.get_model("movimentacoes", "TipoMovimentacao")
    TipoMovimentacao.objects.get_or_create(nome_movimentacao=NOME)


def remover(apps, schema_editor):
    TipoMovimentacao = apps.get_model("movimentacoes", "TipoMovimentacao")
    # `tipo_movimento` é PROTECT: apagar o tipo com movimentação gravada estouraria
    # ProtectedError e travaria o rollback da migração.
    for tipo in TipoMovimentacao.objects.filter(nome_movimentacao=NOME):
        if not tipo.movimentacoes.exists():
            tipo.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("movimentacoes", "0004_popular_catalogo_movimentacao"),
    ]

    operations = [
        migrations.RunPython(criar, remover),
    ]
