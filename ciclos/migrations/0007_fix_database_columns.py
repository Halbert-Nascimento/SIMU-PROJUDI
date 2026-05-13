"""
Alinha as colunas reais do banco com o que o Django espera após a
migration 0006 (que foi state-only).
"""

from django.db import migrations


def _column_exists(cursor, table, column):
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        [table, column],
    )
    return cursor.fetchone()[0] > 0


def _col_type(cursor, table, column):
    cursor.execute(
        "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        [table, column],
    )
    row = cursor.fetchone()
    return row[0] if row else None


def fix_columns(apps, schema_editor):
    cursor = schema_editor.connection.cursor()

    # 1. ciclo_simulacao.id_status_ciclo → status_ciclo_id
    if _column_exists(cursor, "ciclo_simulacao", "id_status_ciclo"):
        cursor.execute(
            "ALTER TABLE ciclo_simulacao RENAME COLUMN id_status_ciclo TO status_ciclo_id"
        )

    # 2. ciclo_simulacao.periodo VARCHAR → INT
    if _col_type(cursor, "ciclo_simulacao", "periodo") != "int":
        cursor.execute(
            "UPDATE ciclo_simulacao SET periodo = 0 "
            "WHERE periodo = '' OR periodo IS NULL"
        )
        cursor.execute(
            "ALTER TABLE ciclo_simulacao MODIFY COLUMN periodo INT NOT NULL"
        )

    # 3. membro_grupo.grupotrabalho_id → grupo_id
    if _column_exists(cursor, "membro_grupo", "grupotrabalho_id"):
        cursor.execute(
            "ALTER TABLE membro_grupo RENAME COLUMN grupotrabalho_id TO grupo_id"
        )

    # 4. participante_ciclo.ciclosimulacao_id → ciclo_id
    if _column_exists(cursor, "participante_ciclo", "ciclosimulacao_id"):
        cursor.execute(
            "ALTER TABLE participante_ciclo RENAME COLUMN ciclosimulacao_id TO ciclo_id"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ciclos", "0006_alter_ciclosimulacao_coordenador_and_more"),
    ]

    operations = [
        migrations.RunPython(fix_columns, migrations.RunPython.noop),
    ]
