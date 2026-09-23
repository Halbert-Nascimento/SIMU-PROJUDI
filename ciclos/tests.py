from __future__ import annotations

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from notificacoes.models import Notificacao, TipoNotificacao
from usuarios.models import VERSAO_TERMOS_ATUAL, Usuario

from .models import CargoSimulacao, CicloSimulacao, GrupoTrabalho, StatusCiclo

def _aceite_termos_teste():
    """Aceite dos termos já registrado: evita que os testes de HTTP caiam no
    portão acesso.middleware.TermosAceitosMiddleware. Função, não dicionário
    de módulo — um dicionário fixaria `timezone.now()` no instante em que o
    módulo é importado, não em que o usuário de teste é criado."""
    return {
        "aceitou_termos_em": timezone.now(),
        "versao_termos_aceita": VERSAO_TERMOS_ATUAL,
    }


class CenarioCicloTestCase(TestCase):
    """Fixture enxuta: 1 ciclo 'Em andamento', 1 grupo, coordenador original + novo + admin + aluno."""

    @classmethod
    def setUpTestData(cls):
        # get_or_create porque a migração de catálogo (movimentacoes.0004) já semeia os
        # cinco cargos: com create(), `cod` unique estoura IntegrityError no setUpClass.
        cls.cargo, _ = CargoSimulacao.objects.get_or_create(
            cod="APA", defaults={"nome": "Advogados Polo Ativo"},
        )
        cls.status_andamento, _ = StatusCiclo.objects.get_or_create(nome_status="Em andamento")

        cls.professor_original = Usuario.objects.create_user(
            username="prof.original", email="prof.original@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.PROFESSOR,
            **_aceite_termos_teste(),
        )
        cls.professor_novo = Usuario.objects.create_user(
            username="prof.novo", email="prof.novo@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.PROFESSOR,
            **_aceite_termos_teste(),
        )
        cls.admin = Usuario.objects.create_user(
            username="admin.teste", email="admin.teste@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ADMIN,
            **_aceite_termos_teste(),
        )
        cls.aluno = Usuario.objects.create_user(
            username="aluno.teste", email="aluno.teste@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
            **_aceite_termos_teste(),
        )

        cls.ciclo = CicloSimulacao.objects.create(
            nome_edicao="Ciclo de Teste", coordenador=cls.professor_original,
            semestre=1, ano=2026, status=cls.status_andamento,
        )
        cls.grupo = GrupoTrabalho.objects.create(
            ciclo=cls.ciclo, cargo_simulacao=cls.cargo, nome="Grupo Teste",
        )

    def cliente_logado(self, usuario):
        client = Client()
        client.force_login(usuario)
        return client


class AdicionarMembroNotificacaoTests(CenarioCicloTestCase):
    def test_adicionar_membro_notifica_o_aluno(self):
        client = self.cliente_logado(self.professor_original)

        with self.captureOnCommitCallbacks(execute=True):
            resp = client.post(
                reverse("ciclos:adicionar_membro", args=[self.ciclo.pk, self.grupo.pk]),
                data={"usuario_id": self.aluno.pk},
            )

        self.assertEqual(resp.json().get("sucesso"), True)
        notificacao = Notificacao.objects.get(
            tipo=TipoNotificacao.CICLO_PARTICIPANTE_ADICIONADO, destinatario=self.aluno,
        )
        self.assertIn(self.ciclo.nome_edicao, notificacao.mensagem)


class EditarCicloCoordenadorNotificacaoTests(CenarioCicloTestCase):
    def _dados_edicao(self, **overrides):
        dados = {
            "nome_edicao": self.ciclo.nome_edicao,
            "semestre": "1",
            "ano": self.ciclo.ano,
            "periodo": 0,
            "status": self.status_andamento.pk,
        }
        dados.update(overrides)
        return dados

    def test_admin_reatribui_coordenador_notifica_o_novo(self):
        client = self.cliente_logado(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            resp = client.post(
                reverse("ciclos:editar_ciclo", args=[self.ciclo.pk]),
                data=self._dados_edicao(coordenador=self.professor_novo.pk),
            )

        self.assertEqual(resp.status_code, 302)
        notificacao = Notificacao.objects.get(
            tipo=TipoNotificacao.CICLO_COORDENADOR_ATRIBUIDO, destinatario=self.professor_novo,
        )
        self.assertIn(self.ciclo.nome_edicao, notificacao.mensagem)
        self.assertFalse(
            Notificacao.objects.filter(
                tipo=TipoNotificacao.CICLO_COORDENADOR_ATRIBUIDO, destinatario=self.professor_original,
            ).exists()
        )

    def test_reenviar_sem_trocar_coordenador_nao_notifica(self):
        client = self.cliente_logado(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            resp = client.post(
                reverse("ciclos:editar_ciclo", args=[self.ciclo.pk]),
                data=self._dados_edicao(coordenador=self.professor_original.pk),
            )

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            Notificacao.objects.filter(tipo=TipoNotificacao.CICLO_COORDENADOR_ATRIBUIDO).exists()
        )

    def test_criar_proprio_ciclo_nao_notifica_o_criador(self):
        client = self.cliente_logado(self.professor_novo)

        with self.captureOnCommitCallbacks(execute=True):
            client.post(reverse("ciclos:criar_ciclo"), data={
                "nome_edicao": "Outro Ciclo de Teste",
                "semestre": "1",
                "ano": 2026,
                "periodo": 0,
            })

        # confirma que o ciclo foi criado de verdade (senão a ausência de
        # notificação seria só porque a criação falhou, não pela regra em si)
        self.assertTrue(
            CicloSimulacao.objects.filter(
                nome_edicao="Outro Ciclo de Teste", coordenador=self.professor_novo,
            ).exists()
        )
        self.assertFalse(
            Notificacao.objects.filter(
                tipo=TipoNotificacao.CICLO_COORDENADOR_ATRIBUIDO, destinatario=self.professor_novo,
            ).exists()
        )
