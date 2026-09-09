# Repontamento de FK: MovimentacaoProcessual saiu do app `processos` e passou
# a morar em `movimentacoes` (mesma tabela `movimentacao_processual`). Só o
# estado do Django muda — a coluna `feedback_professor.movimentacao_id` e a
# tabela referenciada continuam idênticas, então nada acontece no banco.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avaliacoes', '0001_initial'),
        ('movimentacoes', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[
            migrations.AlterField(
                model_name='feedbackprofessor',
                name='movimentacao',
                field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='movimentacoes.movimentacaoprocessual'),
            ),
        ], database_operations=[]),
    ]
