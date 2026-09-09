# Remove do estado do app `processos` os models de movimentação, que passaram
# a morar no app `movimentacoes` (ver movimentacoes/0001_initial). As tabelas
# `tipo_movimentacao`, `movimentacao_processual` e `documento_anexado`
# continuam intactas no banco — aqui só o estado do Django é ajustado
# (SeparateDatabaseAndState / database_operations vazio).
#
# Ordem no grafo: movimentacoes.0001 (cria o estado novo) →
# avaliacoes.0002 (reaponta a FK de FeedbackProfessor) → esta migration
# (remove o estado antigo).

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
