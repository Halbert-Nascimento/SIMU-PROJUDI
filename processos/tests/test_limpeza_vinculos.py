from __future__ import annotations

from importlib import import_module

from django.apps import apps as registro_de_apps

from ciclos.models import GrupoTrabalho
from processos.models import GrupoProcesso

from .fixtures import CenarioMovimentacoesTestCase

MIGRACAO = import_module("processos.migrations.0012_grupoprocesso_uniq_grupo_por_processo")


class LimpezaDeVinculosDuplicadosTests(CenarioMovimentacoesTestCase):
    """
    A limpeza da migração 0012 apaga vínculo e não tem volta — `grupo_processo` das
    movimentações daquele grupo é SET_NULL. Os critérios de escolha ficam fixados aqui.

    O caso de par (processo, grupo) repetido não é testável depois da constraint existir: o
    banco recusa criar o cenário. Ele cobre bancos onde a duplicata é anterior à migração.
    """

    def limpar(self):
        MIGRACAO.limpar_duplicados(registro_de_apps, None)

    def grupo_extra(self, cod, nome):
        return GrupoTrabalho.objects.create(
            ciclo=self.ciclo, cargo_simulacao=self.cargos[cod], nome=nome,
        )

    def test_fica_o_vinculo_que_ja_atuou_no_processo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        original = GrupoProcesso.objects.get(processo=processo, grupo=self.grupos["APP"])
        intruso = GrupoProcesso.objects.create(
            processo=processo, grupo=self.grupo_extra("APP", "Grupo APP fora"),
        )
        # quem atuou é o intruso: a escolha não pode ser pela ordem de criação
        self.registrar(
            processo, "Juntada de Documentos", self.usuarios["APP"], grupo_processo=intruso,
        )

        self.limpar()

        self.assertTrue(GrupoProcesso.objects.filter(pk=intruso.pk).exists())
        self.assertFalse(GrupoProcesso.objects.filter(pk=original.pk).exists())

    def test_no_empate_fica_o_mais_antigo(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        original = GrupoProcesso.objects.get(processo=processo, grupo=self.grupos["APP"])
        intruso = GrupoProcesso.objects.create(
            processo=processo, grupo=self.grupo_extra("APP", "Grupo APP fora"),
        )

        self.limpar()

        self.assertTrue(GrupoProcesso.objects.filter(pk=original.pk).exists())
        self.assertFalse(GrupoProcesso.objects.filter(pk=intruso.pk).exists())

    def test_serventia_duplicada_nao_e_tocada(self):
        """Ciclo com dois grupos de cartório é legítimo, e os dois precisam do vínculo."""
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA"])
        segunda_serventia = GrupoProcesso.objects.create(
            processo=processo, grupo=self.grupo_extra("SC", "Serventia dois"),
        )

        self.limpar()

        self.assertEqual(
            GrupoProcesso.objects.filter(
                processo=processo, grupo__cargo_simulacao__cod="SC",
            ).count(),
            2,
        )
        self.assertTrue(GrupoProcesso.objects.filter(pk=segunda_serventia.pk).exists())

    def test_processo_sem_duplicata_fica_intacto(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "MP", "JZ"])
        antes = set(GrupoProcesso.objects.filter(processo=processo).values_list("pk", flat=True))

        self.limpar()

        self.assertEqual(
            set(GrupoProcesso.objects.filter(processo=processo).values_list("pk", flat=True)),
            antes,
        )
