# Completa a mudança de app: funde os ContentType/Permission órfãos de
# `processos` nos de `movimentacoes` (SeparateDatabaseAndState não mexe nessas
# linhas). Guarda por existência — no-op em banco sem os registros antigos.

from django.db import migrations

MODELOS = ("tipomovimentacao", "movimentacaoprocessual", "documentoanexado")


def fundir(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    try:
        LogEntry = apps.get_model("admin", "LogEntry")
    except LookupError:
        LogEntry = None

    for model in MODELOS:
        antigo = ContentType.objects.filter(app_label="processos", model=model).first()
        if antigo is None:
            continue
        novo, _ = ContentType.objects.get_or_create(app_label="movimentacoes", model=model)

        codenames_no_novo = set(
            Permission.objects.filter(content_type=novo).values_list("codename", flat=True)
        )
        Permission.objects.filter(content_type=antigo).exclude(
            codename__in=codenames_no_novo
        ).update(content_type=novo)
        Permission.objects.filter(content_type=antigo).delete()

        if LogEntry is not None:
            LogEntry.objects.filter(content_type=antigo).update(content_type=novo)

        antigo.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("movimentacoes", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fundir, migrations.RunPython.noop),
    ]
