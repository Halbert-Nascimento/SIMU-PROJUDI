"""
Alinha as colunas da tabela grupo_processo com o que o Django espera
após a migration 0004 (que foi state-only para os through models).
"""

from django.db import migrations


def _column_exists(cursor, table, column):
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        [table, column],
    )
    return cursor.fetchone()[0] > 0


def fix_columns(apps, schema_editor):
    cursor = schema_editor.connection.cursor()

    # grupo_processo.processojudicial_id → processo_id
    if _column_exists(cursor, "grupo_processo", "processojudicial_id"):
        cursor.execute(
            "ALTER TABLE grupo_processo RENAME COLUMN processojudicial_id TO processo_id"
        )

    # grupo_processo.grupotrabalho_id → grupo_id
    if _column_exists(cursor, "grupo_processo", "grupotrabalho_id"):
        cursor.execute(
            "ALTER TABLE grupo_processo RENAME COLUMN grupotrabalho_id TO grupo_id"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("processos", "0004_tipomovimentacao_and_more"),
    ]

    operations = [
        migrations.RunPython(fix_columns, migrations.RunPython.noop),
    ]
