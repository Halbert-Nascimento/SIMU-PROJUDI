from django.db import migrations


def rename_gabinete_to_juiz(apps, schema_editor):
    CargoSimulacao = apps.get_model("ciclos", "CargoSimulacao")
    CargoSimulacao.objects.filter(cod="GJ").update(nome="Juiz", cod="JZ")


def revert(apps, schema_editor):
    CargoSimulacao = apps.get_model("ciclos", "CargoSimulacao")
    CargoSimulacao.objects.filter(cod="JZ").update(nome="Gabinete do Juiz", cod="GJ")


class Migration(migrations.Migration):
    dependencies = [
        ("ciclos", "0004_cargosimulacao_cod_alter_cargosimulacao_nome"),
    ]

    operations = [
        migrations.RunPython(rename_gabinete_to_juiz, revert),
    ]
