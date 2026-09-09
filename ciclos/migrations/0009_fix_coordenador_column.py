"""
A migration 0006 alterou o db_column de CicloSimulacao.coordenador para
'professor_id' como operação state-only (assumindo que o banco alvo já
tinha a coluna com esse nome). Isso nunca aconteceu: tanto em bancos
legados quanto em bancos novos criados via `migrate` a partir da 0001,
a coluna física permanece 'coordenador_id'. Esta migration corrige a
coluna física para ficar consistente com o state esperado pelo Django.
"""

from django.db import migrations


def _column_exists(cursor, table, column):
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        [table, column],
    )
    return cursor.fetchone()[0] > 0


def fix_column(apps, schema_editor):
    cursor = schema_editor.connection.cursor()

    if _column_exists(cursor, "ciclo_simulacao", "coordenador_id") and not _column_exists(
        cursor, "ciclo_simulacao", "professor_id"
    ):
        cursor.execute(
            "ALTER TABLE ciclo_simulacao RENAME COLUMN coordenador_id TO professor_id"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ciclos", "0008_alter_ciclosimulacao_periodo"),
    ]

    operations = [
        migrations.RunPython(fix_column, migrations.RunPython.noop),
    ]
