from django.test import TestCase
from django.urls import reverse

from avaliacoes.models import FeedbackProfessor
from ciclos.models import (
    CargoSimulacao,
    CicloSimulacao,
    GrupoTrabalho,
    ParticipanteCiclo,
    StatusCiclo,
)
from movimentacoes.models import MovimentacaoProcessual, TipoMovimentacao
from processos.models import (
    ClasseProcessual,
    Comarca,
    ProcessoJudicial,
    StatusProcessoJudicial,
    TipoProcesso,
    VaraServentia,
)
from usuarios.models import Usuario


def _criar_usuario(username, perfil):
    return Usuario.objects.create_user(
        username=username,
        email=f"{username}@teste.local",
        password="s3nha-teste",
        tipo_perfil_global=perfil,
    )


class PainelAdministrativoResumoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = _criar_usuario("admin.resumo", Usuario.TipoPerfilGlobal.ADMIN)
        cls.professor = _criar_usuario(
            "prof.resumo", Usuario.TipoPerfilGlobal.PROFESSOR
        )
        cls.professor_participante = _criar_usuario(
            "prof.participante", Usuario.TipoPerfilGlobal.PROFESSOR
        )
        cls.aluno_atual = _criar_usuario(
            "aluno.atual", Usuario.TipoPerfilGlobal.ALUNO
        )
        cls.aluno_encerrado = _criar_usuario(
            "aluno.encerrado", Usuario.TipoPerfilGlobal.ALUNO
        )

        status_andamento = StatusCiclo.objects.create(nome_status="Em andamento")
        status_finalizado = StatusCiclo.objects.create(nome_status="Finalizado")
        cls.ciclo_atual = CicloSimulacao.objects.create(
            nome_edicao="Ciclo atual",
            coordenador=cls.professor,
            semestre=2,
            ano=2026,
            status=status_andamento,
        )
        ciclo_encerrado = CicloSimulacao.objects.create(
            nome_edicao="Ciclo encerrado",
            coordenador=cls.professor,
            semestre=1,
            ano=2026,
            status=status_finalizado,
        )
        cls.ciclo_atual.participantes.add(
            cls.aluno_atual, cls.professor_participante
        )
        ciclo_encerrado.participantes.add(cls.aluno_encerrado)

        cargo = CargoSimulacao.objects.create(nome="Serventia", cod="RESUMO")
        GrupoTrabalho.objects.create(
            ciclo=cls.ciclo_atual, cargo_simulacao=cargo, nome="Grupo atual"
        )
        GrupoTrabalho.objects.create(
            ciclo=ciclo_encerrado, cargo_simulacao=cargo, nome="Grupo encerrado"
        )

        comarca = Comarca.objects.create(nome="Comarca Resumo")
        vara = VaraServentia.objects.create(nome="Vara Resumo", comarca=comarca)
        tipo_processo = TipoProcesso.objects.create(nome="Conhecimento")
        classe = ClasseProcessual.objects.create(nome="Classe Resumo")
        status_processo = StatusProcessoJudicial.objects.create(nome_status="Autuado")
        tipo_movimentacao = TipoMovimentacao.objects.create(
            nome_movimentacao="Movimentação Resumo"
        )

        processo_pendente = cls._criar_processo(
            "0000001-00.2026.8.09.0001", cls.ciclo_atual, vara, tipo_processo,
            classe, status_processo,
        )
        processo_avaliado = cls._criar_processo(
            "0000002-00.2026.8.09.0001", cls.ciclo_atual, vara, tipo_processo,
            classe, status_processo,
        )
        processo_encerrado = cls._criar_processo(
            "0000003-00.2026.8.09.0001", ciclo_encerrado, vara, tipo_processo,
            classe, status_processo,
        )

        MovimentacaoProcessual.objects.create(
            processo=processo_pendente,
            autor=cls.aluno_atual,
            tipo_movimento=tipo_movimentacao,
            descricao_evento="Movimentação pendente",
        )
        movimentacao_avaliada = MovimentacaoProcessual.objects.create(
            processo=processo_avaliado,
            autor=cls.aluno_atual,
            tipo_movimento=tipo_movimentacao,
            descricao_evento="Movimentação avaliada",
        )
        MovimentacaoProcessual.objects.create(
            processo=processo_encerrado,
            autor=cls.aluno_encerrado,
            tipo_movimento=tipo_movimentacao,
            descricao_evento="Movimentação do ciclo encerrado",
        )
        FeedbackProfessor.objects.create(
            movimentacao=movimentacao_avaliada,
            professor=cls.professor,
            comentario="Avaliada",
            nota=8,
        )

    @staticmethod
    def _criar_processo(numero, ciclo, vara, tipo_processo, classe, status):
        return ProcessoJudicial.objects.create(
            numero=numero,
            ciclo=ciclo,
            vara=vara,
            tipo_processo=tipo_processo,
            classe=classe,
            status_atual=status,
        )

    def test_resumo_usa_apenas_dados_dos_ciclos_em_andamento(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse("acesso:painel_administrativo"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["processos_ativos_count"], 2)
        self.assertEqual(resposta.context["avaliacoes_pendentes_count"], 1)
        self.assertEqual(resposta.context["grupos_trabalho_count"], 1)
        self.assertEqual(resposta.context["total_alunos_vinculados"], 1)

    def test_professor_participante_recebe_o_resumo_do_ciclo_vinculado(self):
        self.client.force_login(self.professor_participante)

        resposta = self.client.get(reverse("acesso:painel_administrativo"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Resumo dos ciclos ativos")
        self.assertEqual(resposta.context["processos_ativos_count"], 2)
        self.assertEqual(resposta.context["avaliacoes_pendentes_count"], 1)
        self.assertEqual(resposta.context["grupos_trabalho_count"], 1)
        self.assertEqual(resposta.context["total_alunos_vinculados"], 1)
        self.assertFalse(resposta.context["processos_professor"].exists())


class LoginViewUsuarioLogadoTests(TestCase):
    """A logo do cabeçalho aponta para base:home, que é a própria login_view."""

    @classmethod
    def setUpTestData(cls):
        cls.status_andamento, _ = StatusCiclo.objects.get_or_create(
            nome_status="Em andamento"
        )
        cls.professor = _criar_usuario("prof", Usuario.TipoPerfilGlobal.PROFESSOR)
        cls.ciclo = CicloSimulacao.objects.create(
            nome_edicao="Ciclo de Teste",
            coordenador=cls.professor,
            semestre=1,
            ano=2026,
            status=cls.status_andamento,
        )

    def test_anonimo_ve_o_formulario_de_login(self):
        for rota in ("base:home", "acesso:login"):
            with self.subTest(rota=rota):
                resposta = self.client.get(reverse(rota))
                self.assertEqual(resposta.status_code, 200)
                self.assertTemplateUsed(resposta, "acesso/login.html")

    def test_perfis_de_gestao_vao_para_o_painel(self):
        perfis = (
            Usuario.TipoPerfilGlobal.ADMIN,
            Usuario.TipoPerfilGlobal.COORDENADOR,
            Usuario.TipoPerfilGlobal.PROFESSOR,
        )
        for perfil in perfis:
            usuario = _criar_usuario(f"gestor-{perfil}", perfil)
            self.client.force_login(usuario)
            for rota in ("base:home", "acesso:login"):
                with self.subTest(perfil=perfil, rota=rota):
                    resposta = self.client.get(reverse(rota))
                    self.assertRedirects(
                        resposta,
                        reverse("acesso:painel_administrativo"),
                        fetch_redirect_response=False,
                    )

    def test_aluno_em_ciclo_vai_para_a_area_do_servidor(self):
        aluno = _criar_usuario("aluno-em-ciclo", Usuario.TipoPerfilGlobal.ALUNO)
        ParticipanteCiclo.objects.create(ciclo=self.ciclo, usuario=aluno)
        self.client.force_login(aluno)

        for rota in ("base:home", "acesso:login"):
            with self.subTest(rota=rota):
                resposta = self.client.get(reverse(rota))
                self.assertRedirects(
                    resposta,
                    reverse("processos:pagina_aluno"),
                    fetch_redirect_response=False,
                )

    def test_aluno_sem_ciclo_so_alcanca_a_tela_de_espera(self):
        aluno = _criar_usuario("aluno-sem-ciclo", Usuario.TipoPerfilGlobal.ALUNO)
        self.client.force_login(aluno)

        for rota in ("base:home", "acesso:login"):
            with self.subTest(rota=rota):
                resposta = self.client.get(reverse(rota), follow=True)
                destino, _ = resposta.redirect_chain[-1]
                self.assertEqual(destino, reverse("ciclos:boas_vindas"))
                self.assertEqual(resposta.status_code, 200)
                self.assertTemplateUsed(resposta, "ciclos/boas_vindas.html")

    def test_pendente_ativo_ve_o_formulario_em_vez_de_ser_redirecionado(self):
        # is_active=False é o normal para Pendente; ativo só por edição direta
        pendente = _criar_usuario("pendente-ativo", Usuario.TipoPerfilGlobal.PENDENTE)
        self.client.force_login(pendente)

        for rota in ("base:home", "acesso:login"):
            with self.subTest(rota=rota):
                resposta = self.client.get(reverse(rota))
                self.assertEqual(resposta.status_code, 200)
                self.assertTemplateUsed(resposta, "acesso/login.html")

    def test_perfil_inesperado_ve_o_formulario_em_vez_de_ser_redirecionado(self):
        usuario = _criar_usuario("perfil-invalido", "PerfilQueNaoExiste")
        self.client.force_login(usuario)

        resposta = self.client.get(reverse("acesso:login"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "acesso/login.html")

    def test_post_de_login_com_sessao_ativa_troca_de_conta(self):
        # o redirect vale só para GET: submeter o formulário continua autenticando
        outro = _criar_usuario("outro-gestor", Usuario.TipoPerfilGlobal.ADMIN)
        self.client.force_login(self.professor)

        resposta = self.client.post(
            reverse("acesso:login"),
            {"username": outro.username, "password": "s3nha-teste"},
        )

        self.assertRedirects(
            resposta,
            reverse("acesso:painel_administrativo"),
            fetch_redirect_response=False,
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), outro.pk)

    def test_anonimo_autentica_pelo_formulario(self):
        resposta = self.client.post(
            reverse("acesso:login"),
            {"username": self.professor.username, "password": "s3nha-teste"},
        )
        self.assertRedirects(
            resposta,
            reverse("acesso:painel_administrativo"),
            fetch_redirect_response=False,
        )

    def test_logout_continua_levando_ao_login(self):
        self.client.force_login(self.professor)
        resposta = self.client.post(reverse("acesso:logout"), follow=True)
        self.assertTemplateUsed(resposta, "acesso/login.html")
