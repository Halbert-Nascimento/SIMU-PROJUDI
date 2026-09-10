# State-only: as tabelas já existem; o par que remove o estado em `processos` é processos/0010.

import django.db.models.deletion
import movimentacoes.models
import private_storage.fields
import private_storage.storage.files
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('processos', '0009_add_sequencia_numero_processo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=[
        migrations.CreateModel(
            name='TipoMovimentacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_movimentacao', models.CharField(max_length=45)),
            ],
            options={
                'verbose_name': 'Tipo de Movimentação',
                'verbose_name_plural': 'Tipos de Movimentação',
                'db_table': 'tipo_movimentacao',
            },
        ),
        migrations.CreateModel(
            name='MovimentacaoProcessual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao_evento', models.TextField()),
                ('data_movimento', models.DateTimeField(auto_now_add=True)),
                ('antecedente_logico', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consequentes', to='movimentacoes.movimentacaoprocessual')),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimentacoes', to=settings.AUTH_USER_MODEL)),
                ('movimentacao_origem', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentacoes_derivadas', to='movimentacoes.movimentacaoprocessual')),
                ('processo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes', to='processos.processojudicial')),
                ('tipo_movimento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimentacoes', to='movimentacoes.tipomovimentacao')),
            ],
            options={
                'verbose_name': 'Movimentação Processual',
                'verbose_name_plural': 'Movimentações Processuais',
                'db_table': 'movimentacao_processual',
                'ordering': ['-data_movimento'],
            },
        ),
        migrations.CreateModel(
            name='DocumentoAnexado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo_arquivo', models.CharField(max_length=150)),
                ('caminho_arquivo', private_storage.fields.PrivateFileField(max_length=255, storage=private_storage.storage.files.PrivateFileSystemStorage(), upload_to=movimentacoes.models._upload_to_documento)),
                ('data_upload', models.DateTimeField(auto_now_add=True)),
                ('movimentacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='movimentacoes.movimentacaoprocessual')),
            ],
            options={
                'verbose_name': 'Documento Anexado',
                'verbose_name_plural': 'Documentos Anexados',
                'db_table': 'documento_anexado',
            },
        ),
        ], database_operations=[]),
    ]
