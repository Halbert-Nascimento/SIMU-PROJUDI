# State-only: remove do estado de `processos` os models já recriados em movimentacoes/0001.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processos', '0009_add_sequencia_numero_processo'),
        ('movimentacoes', '0001_initial'),
        ('avaliacoes', '0002_alter_feedbackprofessor_movimentacao'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.RemoveField(
                model_name='movimentacaoprocessual',
                name='antecedente_logico',
            ),
            migrations.RemoveField(
                model_name='movimentacaoprocessual',
                name='autor',
            ),
            migrations.RemoveField(
                model_name='movimentacaoprocessual',
                name='movimentacao_origem',
            ),
            migrations.RemoveField(
                model_name='movimentacaoprocessual',
                name='processo',
            ),
            migrations.RemoveField(
                model_name='movimentacaoprocessual',
                name='tipo_movimento',
            ),
            migrations.DeleteModel(
                name='DocumentoAnexado',
            ),
            migrations.DeleteModel(
                name='MovimentacaoProcessual',
            ),
            migrations.DeleteModel(
                name='TipoMovimentacao',
            ),
        ], database_operations=[]),
    ]
