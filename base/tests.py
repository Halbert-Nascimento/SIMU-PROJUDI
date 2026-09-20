from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.template import Context, Template
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

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
from usuarios.models import Usuario

PERFIL = Usuario.TipoPerfilGlobal
PERFIS_DA_NAVBAR = (PERFIL.ADMIN, PERFIL.COORDENADOR, PERFIL.PROFESSOR, PERFIL.ALUNO)

# Itens que só a navbar completa tem. Nas telas do processo, "Página Inicial"
# é o único item fixo; gestores podem receber também o retorno contextual.
ITENS_QUE_NAO_PODEM_SOBRAR = (
    "Processos", "Cadastrar Processos", "Consultar Todos", "Audiências",
    "Minhas Notas",
)

TELAS_DO_PROCESSO = (
    "processos/templates/processos/cadastro_processo.html",
    "processos/templates/processos/visualizar_processo.html",
    "movimentacoes/templates/movimentacoes/movimentar_processo.html",
    "avaliacoes/templates/avaliacoes/avaliar.html",
)


def trecho_da_navbar(html: str) -> str:
    achado = re.search(r"<nav\b[^>]*sticky[^>]*>.*?</nav>", html, re.DOTALL)
    assert achado, "navbar secundária não encontrada no HTML"
    return achado.group(0)


def renderizar_navbar(usuario, parametros: str = "") -> str:
    return Template("{% load ui %}{% nav_secundaria " + parametros + " %}").render(
        Context({"user": usuario})
    )


class NavbarApenasInicioTests(SimpleTestCase):
    """A tag em si, para cada perfil, sem banco."""

    def test_apenas_inicio_deixa_so_a_pagina_inicial_para_todos_os_perfis(self):
        for perfil in PERFIS_DA_NAVBAR:
            html = renderizar_navbar(Usuario(username="u", tipo_perfil_global=perfil), "apenas_inicio=True")
            self.assertIn("Página Inicial", html, perfil)
            for item in ITENS_QUE_NAO_PODEM_SOBRAR:
                self.assertNotIn(item, html, f"{item!r} sobrou para {perfil}")

    def test_pagina_inicial_leva_a_tela_de_entrada_do_perfil(self):
        aluno = renderizar_navbar(Usuario(username="a", tipo_perfil_global=PERFIL.ALUNO), "apenas_inicio=True")
        professor = renderizar_navbar(Usuario(username="p", tipo_perfil_global=PERFIL.PROFESSOR), "apenas_inicio=True")
        self.assertIn(reverse("processos:pagina_aluno"), aluno)
        self.assertIn(reverse("acesso:painel_administrativo"), professor)

    def test_voltar_ao_processo_so_aparece_para_gestores_com_url_de_retorno(self):
        parametros = "apenas_inicio=True voltar_url='/processos/123/'"
        for perfil in (PERFIL.ADMIN, PERFIL.COORDENADOR, PERFIL.PROFESSOR):
            html = renderizar_navbar(
                Usuario(username="u", tipo_perfil_global=perfil), parametros
            )
            self.assertIn("Voltar ao Processo", html, perfil)
            self.assertIn('href="/processos/123/"', html, perfil)

        aluno = renderizar_navbar(
            Usuario(username="a", tipo_perfil_global=PERFIL.ALUNO), parametros
        )
        self.assertNotIn("Voltar ao Processo", aluno)

    def test_sem_o_parametro_a_navbar_continua_completa(self):
        # as demais telas (Área do Servidor, Minhas Notas) não mudam
        for perfil in PERFIS_DA_NAVBAR:
            html = renderizar_navbar(Usuario(username="u", tipo_perfil_global=perfil), "ativo='inicio'")
            for item in ("Página Inicial", "Processos", "Audiências"):
                self.assertIn(item, html, f"{item!r} sumiu para {perfil}")
        aluno = renderizar_navbar(Usuario(username="a", tipo_perfil_global=PERFIL.ALUNO), "ativo='notas'")
        self.assertIn("Minhas Notas", aluno)


class TelasDoProcessoUsamNavbarReduzidaTests(SimpleTestCase):
    """Trava a regressão nas quatro telas, inclusive Movimentar, que exige catálogo para abrir."""

    def test_cada_tela_do_processo_pede_apenas_inicio(self):
        for caminho in TELAS_DO_PROCESSO:
            fonte = (Path(settings.BASE_DIR) / caminho).read_text(encoding="utf-8")
            chamadas = re.findall(r"\{%\s*nav_secundaria\b[^%]*%\}", fonte)
            self.assertEqual(len(chamadas), 1, caminho)
            self.assertIn("apenas_inicio=True", chamadas[0], caminho)

    def test_telas_fora_da_pagina_principal_informam_o_retorno_do_processo(self):
        for caminho in (
            "movimentacoes/templates/movimentacoes/movimentar_processo.html",
            "avaliacoes/templates/avaliacoes/avaliar.html",
        ):
            fonte = (Path(settings.BASE_DIR) / caminho).read_text(encoding="utf-8")
            self.assertIn("voltar_url=url_processo", fonte, caminho)


class NavbarNasTelasReaisTests(TestCase):
    """As telas do processo abertas de verdade, por perfil."""

    @classmethod
    def setUpTestData(cls):
        status_ciclo = StatusCiclo.objects.get_or_create(nome_status="Em andamento")[0]
        cls.usuarios = {
            perfil: Usuario.objects.create_user(
                username=f"nav.{perfil.value.lower()}", email=f"nav.{perfil.value.lower()}@teste.local",
                password="s3nha-teste", tipo_perfil_global=perfil,
            )
            for perfil in PERFIS_DA_NAVBAR
        }
        professor = cls.usuarios[PERFIL.PROFESSOR]
        cls.ciclo = CicloSimulacao.objects.create(
            nome_edicao="Ciclo Nav", coordenador=professor, semestre=1, ano=2026, status=status_ciclo,
        )
        aluno = cls.usuarios[PERFIL.ALUNO]
        cls.ciclo.participantes.add(aluno)
        cargo = CargoSimulacao.objects.get_or_create(cod="APA", defaults={"nome": "Advogados Polo Ativo"})[0]
        grupo = GrupoTrabalho.objects.create(ciclo=cls.ciclo, cargo_simulacao=cargo, nome="Grupo Nav")
        grupo.membros.add(aluno)

        comarca = Comarca.objects.create(nome="Comarca Nav")
        cls.processo = ProcessoJudicial.objects.create(
            numero="0000001-00.2026.8.09.0001", ciclo=cls.ciclo,
            vara=VaraServentia.objects.create(nome="1ª Vara", comarca=comarca),
            tipo_processo=TipoProcesso.objects.create(nome="Conhecimento"),
            classe=ClasseProcessual.objects.create(nome="Classe"),
            status_atual=StatusProcessoJudicial.objects.get_or_create(nome_status="Autuado")[0],
        )
        GrupoProcesso.objects.create(processo=cls.processo, grupo=grupo)
        tipo = TipoMovimentacao.objects.get_or_create(nome_movimentacao="Petição Teste")[0]
        cls.movimentacao = MovimentacaoProcessual.objects.create(
            processo=cls.processo, autor=aluno, tipo_movimento=tipo, descricao_evento="Evento de teste",
        )

    def cliente(self, perfil):
        client = Client()
        client.force_login(self.usuarios[perfil])
        return client

    def assertNavbarReduzida(self, resposta, contexto):
        self.assertEqual(resposta.status_code, 200, contexto)
        navbar = trecho_da_navbar(resposta.content.decode())
        self.assertIn("Página Inicial", navbar, contexto)
        for item in ITENS_QUE_NAO_PODEM_SOBRAR:
            self.assertNotIn(item, navbar, f"{item!r} sobrou em {contexto}")

    def test_visualizar_processo_para_todos_os_perfis(self):
        url = reverse("processos:visualizar_processo", args=[self.processo.numero])
        for perfil in PERFIS_DA_NAVBAR:
            self.assertNavbarReduzida(self.cliente(perfil).get(url), f"visualizar/{perfil}")

    def test_avaliar_movimentacao_para_quem_avalia(self):
        url = reverse("avaliacoes:avaliar", args=[self.movimentacao.pk])
        for perfil in (PERFIL.ADMIN, PERFIL.COORDENADOR, PERFIL.PROFESSOR):
            resposta = self.cliente(perfil).get(url)
            self.assertEqual(resposta.status_code, 200, f"avaliar/{perfil}")
            navbar = trecho_da_navbar(resposta.content.decode())
            self.assertIn("Voltar ao Processo", navbar, f"avaliar/{perfil}")
            self.assertIn(
                reverse("processos:visualizar_processo", args=[self.processo.numero]),
                navbar,
                f"avaliar/{perfil}",
            )
            for item in ITENS_QUE_NAO_PODEM_SOBRAR:
                self.assertNotIn(item, navbar, f"{item!r} sobrou em avaliar/{perfil}")

    def test_cadastrar_processo_para_quem_tem_ciclo_ativo(self):
        url = reverse("processos:cadastrar_processo")
        for perfil in (PERFIL.PROFESSOR, PERFIL.ALUNO):
            self.assertNavbarReduzida(self.cliente(perfil).get(url), f"cadastrar/{perfil}")

    def test_area_do_servidor_do_aluno_mantem_a_navbar_completa(self):
        resposta = self.cliente(PERFIL.ALUNO).get(reverse("processos:pagina_aluno"))
        self.assertEqual(resposta.status_code, 200)
        navbar = trecho_da_navbar(resposta.content.decode())
        for item in ("Página Inicial", "Processos", "Audiências", "Minhas Notas"):
            self.assertIn(item, navbar)
