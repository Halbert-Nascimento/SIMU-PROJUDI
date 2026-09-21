from __future__ import annotations

import json

from django.test import Client, TestCase
from django.urls import reverse

from ciclos.models import CargoSimulacao, CicloSimulacao, GrupoTrabalho, StatusCiclo
from movimentacoes.models import TipoMovimentacao
from movimentacoes.services import registrar_movimentacao
from processos.models import (
    ClasseProcessual,
    Comarca,
    GrupoProcesso,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
    TipoProcesso,
    VaraServentia,
)
from usuarios.models import Usuario

CARGOS = [
    ("Serventia/Cartório", "SC"),
    ("Advogados Polo Ativo", "APA"),
    ("Advogados Polo Passivo", "APP"),
    ("Ministério Público", "MP"),
    ("Juiz", "JZ"),
]


class CenarioMovimentacoesTestCase(TestCase):
    """Fixture base do módulo de movimentações: 1 ciclo 'Em andamento', 5 grupos (um por cargo), 2 partes."""

    @classmethod
    def setUpTestData(cls):
        cls.cargos = {
            cod: CargoSimulacao.objects.get_or_create(cod=cod, defaults={"nome": nome})[0]
            for nome, cod in CARGOS
        }
        cls.status_andamento, _ = StatusCiclo.objects.get_or_create(nome_status="Em andamento")
        cls.comarca = Comarca.objects.create(nome="Comarca de Teste")
        cls.vara = VaraServentia.objects.create(nome="1ª Vara Cível", comarca=cls.comarca)
        cls.tipo_processo = TipoProcesso.objects.create(nome="Conhecimento")
        cls.classe = ClasseProcessual.objects.create(nome="Procedimento Comum Cível")

        cls.professor = Usuario.objects.create_user(
            username="prof.coord", email="prof.coord@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.PROFESSOR,
        )
        cls.ciclo = CicloSimulacao.objects.create(
            nome_edicao="Ciclo de Teste", coordenador=cls.professor,
            semestre=1, ano=2026, status=cls.status_andamento,
        )

        cls.usuarios = {}
        cls.grupos = {}
        for cod in ("SC", "APA", "APP", "MP", "JZ"):
            u = Usuario.objects.create_user(
                username=f"aluno.{cod.lower()}", email=f"aluno.{cod.lower()}@teste.local",
                password="s3nha-teste", tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
            )
            cls.ciclo.participantes.add(u)
            g = GrupoTrabalho.objects.create(ciclo=cls.ciclo, cargo_simulacao=cls.cargos[cod], nome=f"Grupo {cod}")
            g.membros.add(u)
            cls.usuarios[cod] = u
            cls.grupos[cod] = g

        cls.parte_autor = ParteFicticia.objects.create(
            nome_razao="João da Silva", cpf_cnpj="111.111.111-11", tipo_pessoa=ParteFicticia.TipoPessoa.FISICA,
        )
        cls.parte_reu = ParteFicticia.objects.create(
            nome_razao="Empresa Ré Ltda.", cpf_cnpj="22.222.222/0001-22", tipo_pessoa=ParteFicticia.TipoPessoa.JURIDICA,
        )

    # -- helpers de instância -------------------------------------------------

    def tipo(self, nome):
        return TipoMovimentacao.objects.get(nome_movimentacao=nome)

    def cliente_logado(self, usuario):
        client = Client()
        client.force_login(usuario)
        session = client.session
        session["ciclo_ativo_id"] = self.ciclo.pk
        session.save()
        return client

    def criar_processo_protocolado(self, *, autor=None, segredo_justica=False,
                                    parte_ativo=None, parte_passivo=None):
        """Cria o processo + polos (sem grupo) e registra o Protocolo via registrar_movimentacao real."""
        autor = autor or self.usuarios["APA"]
        processo = ProcessoJudicial.objects.create(
            numero=ProcessoJudicial.gerar_numero_cnj(ano=2026, tr=26, origem=self.comarca.pk),
            ciclo=self.ciclo, vara=self.vara, tipo_processo=self.tipo_processo, classe=self.classe,
            status_atual=self.tipo("Protocolo da Petição Inicial").efeito_status,
            segredo_justica=segredo_justica,
        )
        PoloProcessual.objects.create(processo=processo, parte=parte_ativo or self.parte_autor, tipo_polo="Ativo")
        PoloProcessual.objects.create(processo=processo, parte=parte_passivo or self.parte_reu, tipo_polo="Passivo")
        grupo_autor = autor.grupos_trabalho.filter(ciclo=self.ciclo).first()
        if grupo_autor:
            processo.grupos.add(grupo_autor)
        registrar_movimentacao(
            processo=processo, autor=autor, tipo_movimentacao=self.tipo("Protocolo da Petição Inicial"),
            descricao_evento=f'Processo "{processo.numero}" cadastrado.',
        )
        return processo

    def autuar_processo(self, processo, cods_grupos, *, sc_user=None):
        """Bate na view processos:atribuir_grupo_processos de verdade (não reimplementa a lógica aqui)."""
        client = self.cliente_logado(sc_user or self.usuarios["SC"])
        grupo_ids = [self.grupos[cod].pk for cod in cods_grupos]
        resp = client.post(
            reverse("processos:atribuir_grupo_processos"),
            data=json.dumps({"processo_ids": [processo.pk], "grupo_ids": grupo_ids}),
            content_type="application/json",
        )
        processo.refresh_from_db()
        return resp

    def grupo_processo(self, processo, cod):
        return GrupoProcesso.objects.get(processo=processo, grupo__cargo_simulacao__cod=cod)

    def registrar(self, processo, nome_tipo, autor, *, grupo_processo=None, movimentacao_origem=None):
        return registrar_movimentacao(
            processo=processo, autor=autor, tipo_movimentacao=self.tipo(nome_tipo),
            grupo_processo=grupo_processo, movimentacao_origem=movimentacao_origem,
        )

    def avancar_ate_audiencia_sem_acordo(self, processo):
        """Cadeia real (via registrar_movimentacao) até Contestação/Réplica ficarem praticáveis."""
        gp_sc = self.grupo_processo(processo, "SC")
        gp_jz = self.grupo_processo(processo, "JZ")
        sc, jz = self.usuarios["SC"], self.usuarios["JZ"]
        for nome in [
            "Custas Recolhidas", "Conclusão ao Juiz",
        ]:
            autor, gp = (sc, gp_sc)
            self.registrar(processo, nome, autor, grupo_processo=gp)
        for nome in [
            "Análise da Inicial — Em Ordem", "Despacho de Citação",
        ]:
            self.registrar(processo, nome, jz, grupo_processo=gp_jz)
        for nome in [
            "Modalidade de Citação — Mandado", "Citação por Mandado",
            "Cumprimento do Mandado — Réu Encontrado", "Citação Positiva",
        ]:
            self.registrar(processo, nome, sc, grupo_processo=gp_sc)
        return self.registrar(processo, "Audiência de Conciliação — Sem Acordo", jz, grupo_processo=gp_jz)

    def avancar_ate_publicacao_intimacao(self, processo):
        """Continua a partir de avancar_ate_audiencia_sem_acordo() até 'Publicação/Intimação das Partes'."""
        gp_sc = self.grupo_processo(processo, "SC")
        gp_jz = self.grupo_processo(processo, "JZ")
        gp_app = self.grupo_processo(processo, "APP")
        sc, jz, app = self.usuarios["SC"], self.usuarios["JZ"], self.usuarios["APP"]
        self.registrar(processo, "Contestação", app, grupo_processo=gp_app)
        self.registrar(processo, "Réplica do Autor", app, grupo_processo=gp_app)
        for nome in [
            "MP Deve Intervir — Não", "Decisão Saneadora", "Provas a Produzir — Prova Oral",
            "Audiência de Instrução e Julgamento", "Resultado da Audiência — Memoriais",
        ]:
            self.registrar(processo, nome, jz, grupo_processo=gp_jz)
        self.registrar(processo, "Memoriais/Alegações Finais", app, grupo_processo=gp_app)
        for nome in ["Sentença", "Tipo de Sentença — Com Mérito", "Com resolução do mérito"]:
            self.registrar(processo, nome, jz, grupo_processo=gp_jz)
        return self.registrar(processo, "Publicação/Intimação das Partes", sc, grupo_processo=gp_sc)
