from __future__ import annotations

from django.test import Client, TestCase
from django.utils import timezone

from ciclos.models import CargoSimulacao, CicloSimulacao, GrupoTrabalho, StatusCiclo
from movimentacoes.models import MovimentacaoProcessual, TipoMovimentacao
from processos.models import (
    ClasseProcessual,
    Comarca,
    GrupoProcesso,
    ProcessoJudicial,
    StatusProcessoJudicial,
    TipoProcesso,
    VaraServentia,
)
from usuarios.models import VERSAO_TERMOS_ATUAL, Usuario

PERFIL = Usuario.TipoPerfilGlobal


def criar_usuario(username, perfil):
    # aceite dos termos já registrado: evita que os testes de HTTP caiam no
    # portão acesso.middleware.TermosAceitosMiddleware.
    return Usuario.objects.create_user(
        username=username, email=f"{username}@teste.local", password="s3nha-teste",
        tipo_perfil_global=perfil,
        aceitou_termos_em=timezone.now(), versao_termos_aceita=VERSAO_TERMOS_ATUAL,
    )


class CenarioAvaliacao(TestCase):
    """Um ciclo do professor `prof`, um aluno com uma movimentação e um professor de fora."""

    @classmethod
    def setUpTestData(cls):
        status_ciclo = StatusCiclo.objects.get_or_create(nome_status="Em andamento")[0]
        cls.prof = criar_usuario("prof.estrelas", PERFIL.PROFESSOR)
        cls.prof_fora = criar_usuario("prof.fora", PERFIL.PROFESSOR)
        cls.aluno = criar_usuario("aluno.estrelas", PERFIL.ALUNO)

        cls.ciclo = CicloSimulacao.objects.create(
            nome_edicao="Ciclo Estrelas", coordenador=cls.prof, semestre=1, ano=2026,
            status=status_ciclo,
        )
        cls.ciclo.participantes.add(cls.aluno)
        cargo = CargoSimulacao.objects.get_or_create(cod="APA", defaults={"nome": "Advogados Polo Ativo"})[0]
        grupo = GrupoTrabalho.objects.create(ciclo=cls.ciclo, cargo_simulacao=cargo, nome="Grupo Estrelas")
        grupo.membros.add(cls.aluno)

        comarca = Comarca.objects.create(nome="Comarca Teste")
        cls.processo = ProcessoJudicial.objects.create(
            numero="0000001-00.2026.8.09.0001", ciclo=cls.ciclo,
            vara=VaraServentia.objects.create(nome="1ª Vara", comarca=comarca),
            tipo_processo=TipoProcesso.objects.create(nome="Conhecimento"),
            classe=ClasseProcessual.objects.create(nome="Classe"),
            status_atual=StatusProcessoJudicial.objects.get_or_create(nome_status="Autuado")[0],
        )
        GrupoProcesso.objects.create(processo=cls.processo, grupo=grupo)
        cls.tipo = TipoMovimentacao.objects.get_or_create(nome_movimentacao="Petição Teste")[0]

    def nova_movimentacao(self):
        return MovimentacaoProcessual.objects.create(
            processo=self.processo, autor=self.aluno, tipo_movimento=self.tipo,
            descricao_evento="Evento de teste",
        )

    def cliente(self, usuario):
        client = Client()
        client.force_login(usuario)
        return client
