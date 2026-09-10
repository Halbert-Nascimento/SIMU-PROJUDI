# State-only: reaponta a FK para movimentacoes.MovimentacaoProcessual (mesma tabela).

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
