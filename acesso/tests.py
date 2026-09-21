from django.test import TestCase
from django.urls import reverse

from acesso.forms_admin_usuarios import AtualizarUsuarioForm
from acesso.permissions import pode_alterar_senha
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


class PodeAlterarSenhaTests(TestCase):
    """Hierarquia de acesso.permissions.pode_alterar_senha — usada pelo modal de gestão e por acesso/services.py."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = _criar_usuario("admin.senha", Usuario.TipoPerfilGlobal.ADMIN)
        cls.coordenador = _criar_usuario("coord.senha", Usuario.TipoPerfilGlobal.COORDENADOR)
        cls.professor = _criar_usuario("prof.senha", Usuario.TipoPerfilGlobal.PROFESSOR)
        cls.aluno = _criar_usuario("aluno.senha", Usuario.TipoPerfilGlobal.ALUNO)
        cls.pendente = _criar_usuario("pendente.senha", Usuario.TipoPerfilGlobal.PENDENTE)

    def test_autoalteracao_sempre_permitida(self):
        for usuario in (self.admin, self.coordenador, self.professor, self.aluno, self.pendente):
            with self.subTest(usuario=usuario.username):
                self.assertTrue(pode_alterar_senha(usuario, usuario))

    def test_admin_altera_qualquer_um(self):
        for alvo in (self.coordenador, self.professor, self.aluno, self.pendente):
            with self.subTest(alvo=alvo.username):
                self.assertTrue(pode_alterar_senha(self.admin, alvo))

    def test_coordenador_altera_professor_aluno_e_pendente(self):
        for alvo in (self.professor, self.aluno, self.pendente):
            with self.subTest(alvo=alvo.username):
                self.assertTrue(pode_alterar_senha(self.coordenador, alvo))

    def test_coordenador_nao_altera_outro_coordenador_nem_admin(self):
        outro_coordenador = _criar_usuario("coord.senha.2", Usuario.TipoPerfilGlobal.COORDENADOR)
        for alvo in (outro_coordenador, self.admin):
            with self.subTest(alvo=alvo.username):
                self.assertFalse(pode_alterar_senha(self.coordenador, alvo))

    def test_professor_altera_aluno_e_pendente(self):
        for alvo in (self.aluno, self.pendente):
            with self.subTest(alvo=alvo.username):
                self.assertTrue(pode_alterar_senha(self.professor, alvo))

    def test_professor_nao_altera_professor_coordenador_nem_admin(self):
        outro_professor = _criar_usuario("prof.senha.2", Usuario.TipoPerfilGlobal.PROFESSOR)
        for alvo in (outro_professor, self.coordenador, self.admin):
            with self.subTest(alvo=alvo.username):
                self.assertFalse(pode_alterar_senha(self.professor, alvo))

    def test_aluno_nao_altera_ninguem_alem_de_si(self):
        self.assertFalse(pode_alterar_senha(self.aluno, self.pendente))
        self.assertFalse(pode_alterar_senha(self.aluno, self.professor))


class AtualizarUsuarioFormSenhaTests(TestCase):
    """Seção "Alterar Senha" do modal de gestão — acesso/forms_admin_usuarios.py."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = _criar_usuario("admin.form", Usuario.TipoPerfilGlobal.ADMIN)
        cls.coordenador = _criar_usuario("coord.form", Usuario.TipoPerfilGlobal.COORDENADOR)
        cls.outro_coordenador = _criar_usuario("coord.form.2", Usuario.TipoPerfilGlobal.COORDENADOR)
        cls.professor = _criar_usuario("prof.form", Usuario.TipoPerfilGlobal.PROFESSOR)

    def test_campos_de_senha_vazios_nao_altera_hash(self):
        hash_antes = self.professor.password
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.PROFESSOR,
                "nova_senha": "",
                "confirmacao_senha": "",
            },
            ator=self.coordenador,
            alvo=self.professor,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.aplicar()
        self.professor.refresh_from_db()
        self.assertEqual(hash_antes, self.professor.password)

    def test_preencher_apenas_um_campo_de_senha_e_invalido(self):
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.PROFESSOR,
                "nova_senha": "Senha-Nova-Forte-1",
                "confirmacao_senha": "",
            },
            ator=self.coordenador,
            alvo=self.professor,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("confirmacao_senha", form.errors)

    def test_senhas_diferentes_e_invalido(self):
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.PROFESSOR,
                "nova_senha": "Senha-Nova-Forte-1",
                "confirmacao_senha": "Senha-Diferente-2",
            },
            ator=self.coordenador,
            alvo=self.professor,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("confirmacao_senha", form.errors)

    def test_senha_fraca_dispara_validate_password(self):
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.PROFESSOR,
                "nova_senha": "12345678",
                "confirmacao_senha": "12345678",
            },
            ator=self.coordenador,
            alvo=self.professor,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nova_senha", form.errors)

    def test_coordenador_redefine_senha_de_professor(self):
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.PROFESSOR,
                "nova_senha": "Senha-Nova-Forte-1",
                "confirmacao_senha": "Senha-Nova-Forte-1",
            },
            ator=self.coordenador,
            alvo=self.professor,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.aplicar()
        self.professor.refresh_from_db()
        self.assertTrue(self.professor.check_password("Senha-Nova-Forte-1"))

    def test_coordenador_nao_altera_dados_nem_senha_de_admin(self):
        """Regressão do achado de segurança: tipo ATUAL do alvo, não só o de destino."""
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.PROFESSOR,
                "nova_senha": "Senha-Nova-Forte-1",
                "confirmacao_senha": "Senha-Nova-Forte-1",
            },
            ator=self.coordenador,
            alvo=self.admin,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_coordenador_nao_altera_nem_status_de_outro_coordenador_sem_mexer_em_senha(self):
        """
        pode_alterar_senha() em clean() é um gate do formulário inteiro, não só da senha:
        um Coordenador não pode nem alternar "Ativo" de outro Coordenador por este modal,
        mesmo sem tocar nos campos de senha — é a mesma regra de hierarquia de
        acesso/permissions.py, aplicada de forma consistente ao invés de só à senha.
        """
        form = AtualizarUsuarioForm(
            {
                "is_active": "off",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.COORDENADOR,
                "nova_senha": "",
                "confirmacao_senha": "",
            },
            ator=self.coordenador,
            alvo=self.outro_coordenador,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_coordenador_promove_professor_a_coordenador_e_define_senha_no_mesmo_envio(self):
        """
        Regressão: aplicar() mudava self.alvo.tipo_perfil_global ANTES de chamar
        redefinir_senha(), que reavalia pode_alterar_senha() contra esse tipo já mutado.
        Um Coordenador promovendo um Professor a Coordenador e definindo senha nova no
        mesmo envio via um PermissionError não tratado (clean() aprova contra o tipo
        original do alvo; a ordem em aplicar() não pode invalidar essa aprovação).
        """
        form = AtualizarUsuarioForm(
            {
                "is_active": "on",
                "tipo_perfil_global": Usuario.TipoPerfilGlobal.COORDENADOR,
                "nova_senha": "Senha-Nova-Forte-1",
                "confirmacao_senha": "Senha-Nova-Forte-1",
            },
            ator=self.coordenador,
            alvo=self.professor,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.aplicar()

        self.professor.refresh_from_db()
        self.assertEqual(self.professor.tipo_perfil_global, Usuario.TipoPerfilGlobal.COORDENADOR)
        self.assertTrue(self.professor.check_password("Senha-Nova-Forte-1"))


class UsuariosEditaveisTests(TestCase):
    """
    Regressão: o botão "editar" da tabela de usuários ficava visível em toda linha, mesmo
    quando pode_alterar_senha() bloqueava a submissão no clean() do form — um Professor via
    "editar" em outro Professor, Coordenador ou Admin e só descobria a falta de permissão
    depois de preencher e salvar. usuarios_editaveis (usuario_lista e painel_administrativo,
    acesso/views_admin_usuarios.py) filtra a exibição pela mesma regra de hierarquia, e
    exclui também o próprio ator porque usuario_atualizar() já bloqueia autoedição por
    esta tela.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = _criar_usuario("admin.editaveis", Usuario.TipoPerfilGlobal.ADMIN)
        cls.coordenador = _criar_usuario("coord.editaveis", Usuario.TipoPerfilGlobal.COORDENADOR)
        cls.professor = _criar_usuario("prof.editaveis", Usuario.TipoPerfilGlobal.PROFESSOR)
        cls.outro_professor = _criar_usuario("prof.editaveis.2", Usuario.TipoPerfilGlobal.PROFESSOR)
        cls.aluno = _criar_usuario("aluno.editaveis", Usuario.TipoPerfilGlobal.ALUNO)

    def test_usuario_lista_esconde_professor_coordenador_e_admin_para_professor(self):
        self.client.force_login(self.professor)

        resposta = self.client.get(reverse("acesso:usuario_lista"))

        editaveis = resposta.context["usuarios_editaveis"]
        self.assertIn(self.aluno.pk, editaveis)
        self.assertNotIn(self.outro_professor.pk, editaveis)
        self.assertNotIn(self.coordenador.pk, editaveis)
        self.assertNotIn(self.admin.pk, editaveis)

    def test_usuario_lista_exclui_o_proprio_ator_da_edicao(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse("acesso:usuario_lista"))

        self.assertNotIn(self.admin.pk, resposta.context["usuarios_editaveis"])

    def test_painel_administrativo_aplica_a_mesma_regra_de_hierarquia(self):
        self.client.force_login(self.professor)

        resposta = self.client.get(reverse("acesso:painel_administrativo"))

        editaveis = resposta.context["usuarios_editaveis"]
        self.assertIn(self.aluno.pk, editaveis)
        self.assertNotIn(self.outro_professor.pk, editaveis)
        self.assertNotIn(self.professor.pk, editaveis)


class MinhaContaViewTests(TestCase):
    """Autoalteração de senha — acesso/views.py:minha_conta."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = _criar_usuario("autoalteracao", Usuario.TipoPerfilGlobal.ALUNO)

    def test_senha_atual_incorreta_e_rejeitada(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(
            reverse("acesso:minha_conta"),
            {
                "old_password": "senha-errada",
                "new_password1": "Senha-Nova-Forte-1",
                "new_password2": "Senha-Nova-Forte-1",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("s3nha-teste"))
        # O erro aparece só inline (form.<campo>.errors), não duplicado via messages —
        # a view reexibe o form no mesmo request, então propagar_erros_form duplicaria.
        self.assertEqual(len(list(resposta.context["messages"])), 0)
        self.assertTrue(resposta.context["form"].errors.get("old_password"))

    def test_senha_nova_fraca_e_rejeitada(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(
            reverse("acesso:minha_conta"),
            {
                "old_password": "s3nha-teste",
                "new_password1": "12345678",
                "new_password2": "12345678",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("s3nha-teste"))

    def test_troca_com_sucesso_mantem_sessao_ativa(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(
            reverse("acesso:minha_conta"),
            {
                "old_password": "s3nha-teste",
                "new_password1": "Senha-Nova-Forte-1",
                "new_password2": "Senha-Nova-Forte-1",
            },
        )
        self.assertRedirects(resposta, reverse("acesso:minha_conta"))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("Senha-Nova-Forte-1"))

        # Sessão não foi derrubada pela troca de senha (update_session_auth_hash).
        resposta_seguinte = self.client.get(reverse("acesso:minha_conta"))
        self.assertEqual(resposta_seguinte.status_code, 200)

    def test_aluno_sem_ciclo_ainda_alcanca_minha_conta(self):
        """
        Regressão: AlunoSemCicloMiddleware prendia o Aluno sem ciclo numa lista fechada de
        rotas liberadas (ver ciclos/middleware.py) e não incluía minha_conta — o Aluno preso
        na tela de boas-vindas não conseguia trocar a própria senha.
        """
        self.assertFalse(self.usuario.ciclos_participados.exists())
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("acesso:minha_conta"))

        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "acesso/minha_conta.html")

    def test_tela_mostra_breadcrumb_e_link_de_volta(self):
        """A tela precisa deixar claro onde o usuário está e como voltar ao painel/área dele."""
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("acesso:minha_conta"))

        self.assertContains(resposta, "Minha Conta")
        self.assertContains(resposta, "Voltar para")
        self.assertContains(resposta, reverse("base:home"))


class PainelAdministrativoModalSenhaTests(TestCase):
    """
    Regressão: painel_administrativo.html tem um modal de "Editar/Aprovar Usuário"
    inteiramente separado do de usuario_lista.html (mesma view usuario_atualizar, HTML e
    JS próprios — abrirEdicao/fecharEdicao, ids "edicao-*"). A seção "Alterar Senha" foi
    implementada primeiro só em usuario_lista.html; este teste garante que o modal
    realmente usado (painel_administrativo é o LOGIN_REDIRECT_URL) também a tenha.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = _criar_usuario("admin.painel.senha", Usuario.TipoPerfilGlobal.ADMIN)

    def test_modal_do_painel_tem_secao_de_alterar_senha(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse("acesso:painel_administrativo"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Alterar Senha")
        self.assertContains(resposta, 'name="nova_senha"')
        self.assertContains(resposta, 'name="confirmacao_senha"')
        self.assertContains(resposta, 'id="edicao-senha-accordion-header"')
