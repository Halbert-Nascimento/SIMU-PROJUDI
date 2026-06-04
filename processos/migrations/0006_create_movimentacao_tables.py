"""
Cria as tabelas tipo_movimentacao, movimentacao_processual e
documento_anexado no banco.  A migration 0004 registrou os models
apenas no state — aqui criamos as tabelas de fato.
"""

from django.db import migrations


def create_tables(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for model_name, table_name in [
            ("TipoMovimentacao", "tipo_movimentacao"),
            ("MovimentacaoProcessual", "movimentacao_processual"),
            ("DocumentoAnexado", "documento_anexado"),
        ]:
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            if not cursor.fetchone():
                model = apps.get_model("processos", model_name)
                schema_editor.create_model(model)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("processos", "0005_fix_grupo_processo_columns"),
    ]

    operations = [
        migrations.RunPython(create_tables, migrations.RunPython.noop),
    ]
