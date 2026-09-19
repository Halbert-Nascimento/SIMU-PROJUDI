from django.test import TestCase
from django.urls import reverse

from ciclos.models import CicloSimulacao, ParticipanteCiclo, StatusCiclo
from usuarios.models import Usuario


def _criar_usuario(username, perfil):
    return Usuario.objects.create_user(
        username=username,
        email=f"{username}@teste.local",
        password="s3nha-teste",
        tipo_perfil_global=perfil,
    )


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
