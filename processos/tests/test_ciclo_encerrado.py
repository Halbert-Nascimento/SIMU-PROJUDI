"""
Ciclo fora de "Em andamento" é só consulta: nenhum perfil escreve nos autos.
Consulta, avaliação do professor e gestão do próprio ciclo continuam liberadas.
"""

from __future__ import annotations

import json

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse

from ciclos.models import CicloSimulacao, GrupoTrabalho, StatusCiclo
from movimentacoes.models import MovimentacaoProcessual
from movimentacoes.permissions import (
    pode_editar_movimentacao,
    pode_movimentar_processo,
    pode_praticar_movimentacao,
)
from processos.models import GrupoProcesso, ProcessoJudicial
from processos.permissions import pode_editar_processo
from processos.tests.fixtures import CenarioMovimentacoesTestCase, aceite_termos_teste
from processos.views import atribuir_grupo_processos, cadastrar_processo
from usuarios.models import Usuario

STATUS_ENCERRADOS = ("Arquivado", "Finalizado")
AVISO = "Ciclo encerrado"


class _CenarioComProcesso(CenarioMovimentacoesTestCase):
    def setUp(self):
        self.processo = self.criar_processo_protocolado()
        self.autuar_processo(self.processo, ["APA", "APP"])
        self.grupo_apa = self.grupo_processo(self.processo, "APA")
        self.movimentacao = self.registrar(
            self.processo,
            "Juntada de Documentos",
            self.usuarios["APA"],
            grupo_processo=self.grupo_apa,
        )
        # aluno só com ciclo encerrado é desviado pelo middleware antes da view
        outro = CicloSimulacao.objects.create(
            nome_edicao="Outro ciclo aberto",
            coordenador=self.professor,
            semestre=2,
            ano=2026,
            status=self.status_andamento,
        )
        outro.participantes.add(*self.usuarios.values())

    def mudar_status(self, nome):
        status, _ = StatusCiclo.objects.get_or_create(nome_status=nome)
        self.ciclo.status = status
        self.ciclo.save(update_fields=["status"])
        # a instância em memória carregaria o status anterior nas funções puras
        self.processo = ProcessoJudicial.objects.get(pk=self.processo.pk)

    def mantenedores(self):
        extras = []
        for perfil in (
            Usuario.TipoPerfilGlobal.ADMIN,
            Usuario.TipoPerfilGlobal.COORDENADOR,
        ):
            usuario, _ = Usuario.objects.get_or_create(
                username=f"{perfil.lower()}.ciclo",
                defaults={
                    "email": f"{perfil.lower()}.ciclo@teste.local",
                    "tipo_perfil_global": perfil,
                    **aceite_termos_teste(),
                },
            )
            extras.append(usuario)
        return [self.usuarios["SC"], self.professor, *extras]

    def corpo_dados(self):
        return {
            "vara_id": self.vara.pk,
            "tipo_processo_id": self.tipo_processo.pk,
            "classe_id": self.classe.pk,
            "valor_causa": "123,45",
            "segredo_justica": True,
        }

    def corpo_parte(self):
        return {
            "parte_id": self.parte_autor.pk,
            "nome_razao": "Nome Alterado",
            "cpf_cnpj": self.parte_autor.cpf_cnpj,
            "tipo_pessoa": self.parte_autor.tipo_pessoa,
        }

    def post_json(self, usuario, rota, corpo):
        return self.cliente_logado(usuario).post(
            reverse(rota, args=[self.processo.numero]),
            data=json.dumps(corpo),
            content_type="application/json",
        )


class EscritaEmCicloEncerradoTests(_CenarioComProcesso):
    def test_funcoes_de_permissao_negam_para_todos_os_perfis(self):
        for nome in STATUS_ENCERRADOS:
            self.mudar_status(nome)
            for usuario in self.mantenedores():
                with self.subTest(status=nome, usuario=usuario.username):
                    self.assertFalse(pode_editar_processo(usuario, self.processo))
            apa = self.usuarios["APA"]
            with self.subTest(status=nome, regra="movimentação"):
                self.assertFalse(pode_movimentar_processo(apa, self.processo))
                self.assertFalse(
                    pode_praticar_movimentacao(
                        apa, self.processo, self.tipo("Juntada de Documentos")
                    )
                )
                self.assertFalse(
                    pode_editar_movimentacao(apa, self.processo, self.movimentacao)
                )

    def test_registrar_e_corrigir_movimentacao_sao_recusados(self):
        rotas = (
            reverse("movimentacoes:criar_movimentacao", args=[self.processo.numero]),
            reverse(
                "movimentacoes:editar_movimentacao",
                args=[self.processo.numero, self.movimentacao.pk],
            ),
        )
        corpo = {
            "tipo_movimento": self.tipo("Juntada de Documentos").pk,
            "descricao_evento": "fora do prazo",
            "corrige_anterior": "on",
        }
        for nome in STATUS_ENCERRADOS:
            self.mudar_status(nome)
            cliente = self.cliente_logado(self.usuarios["APA"])
            antes = MovimentacaoProcessual.objects.count()
            for rota in rotas:
                with self.subTest(status=nome, rota=rota):
                    self.assertEqual(cliente.get(rota).status_code, 403)
                    self.assertEqual(cliente.post(rota, corpo).status_code, 403)
                    self.assertEqual(MovimentacaoProcessual.objects.count(), antes)

    def test_dados_do_processo_nao_mudam(self):
        for nome in STATUS_ENCERRADOS:
            self.mudar_status(nome)
            for usuario in self.mantenedores():
                with self.subTest(status=nome, usuario=usuario.username):
                    resposta = self.post_json(
                        usuario,
                        "processos:modificar_dados_processo",
                        self.corpo_dados(),
                    )
                    self.assertEqual(resposta.status_code, 403)
                    self.assertIn(AVISO, resposta.json()["erro"])
                    self.processo.refresh_from_db()
                    self.assertFalse(self.processo.segredo_justica)

    def test_dados_da_parte_nao_mudam(self):
        nome_original = self.parte_autor.nome_razao
        for nome in STATUS_ENCERRADOS:
            self.mudar_status(nome)
            for usuario in self.mantenedores():
                with self.subTest(status=nome, usuario=usuario.username):
                    resposta = self.post_json(
                        usuario, "processos:alterar_parte", self.corpo_parte()
                    )
                    self.assertEqual(resposta.status_code, 403)
                    self.assertIn(AVISO, resposta.json()["erro"])
                    self.parte_autor.refresh_from_db()
                    self.assertEqual(self.parte_autor.nome_razao, nome_original)

    def test_tela_do_processo_nao_oferece_escrita_e_explica_o_motivo(self):
        for nome in STATUS_ENCERRADOS:
            self.mudar_status(nome)
            for cod in ("APA", "SC"):
                with self.subTest(status=nome, usuario=cod):
                    resposta = self.cliente_logado(self.usuarios[cod]).get(
                        reverse(
                            "processos:visualizar_processo",
                            args=[self.processo.numero],
                        )
                    )
                    self.assertEqual(resposta.status_code, 200)
                    self.assertFalse(resposta.context["pode_editar_processo"])
                    self.assertFalse(resposta.context["pode_movimentar_processo"])
                    self.assertFalse(
                        any(m["pode_editar"] for m in resposta.context["movimentacoes"])
                    )
                    self.assertContains(resposta, AVISO)
                    self.assertNotContains(resposta, "/movimentar/")

    def test_distribuir_e_cadastrar_recusam_mesmo_sem_o_middleware(self):
        # o middleware já não entrega ciclo encerrado; a view não pode depender disso
        self.mudar_status("Arquivado")
        fabrica = RequestFactory()

        requisicao = fabrica.post(
            "/",
            data=json.dumps(
                {
                    "processo_ids": [self.processo.pk],
                    "grupo_ids_adicionar": [self.grupos["JZ"].pk],
                }
            ),
            content_type="application/json",
        )
        requisicao.user = self.usuarios["SC"]
        requisicao.ciclo_ativo = self.ciclo
        resposta = atribuir_grupo_processos(requisicao)
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(
            GrupoProcesso.objects.filter(
                processo=self.processo, grupo=self.grupos["JZ"]
            ).exists()
        )

        requisicao = fabrica.get("/processos/cadastrar/")
        requisicao.user = self.usuarios["APA"]
        requisicao.ciclo_ativo = self.ciclo
        with self.assertRaises(PermissionDenied):
            cadastrar_processo(requisicao)


class CicloAbertoEExcecoesTests(_CenarioComProcesso):
    """Regressão: o que já funcionava continua funcionando."""

    def test_ciclo_em_andamento_grava_sem_diferenciar_caixa(self):
        for nome in ("Em andamento", "EM ANDAMENTO"):
            with self.subTest(status=nome):
                self.ciclo.status.nome_status = nome
                self.ciclo.status.save()
                resposta = self.post_json(
                    self.usuarios["SC"],
                    "processos:modificar_dados_processo",
                    self.corpo_dados(),
                )
                self.assertEqual(resposta.status_code, 200)
                resposta = self.post_json(
                    self.usuarios["SC"], "processos:alterar_parte", self.corpo_parte()
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(
                    pode_movimentar_processo(self.usuarios["APA"], self.processo)
                )

    def test_consulta_e_avaliacao_continuam_em_ciclo_encerrado(self):
        self.mudar_status("Finalizado")
        cliente = self.cliente_logado(self.professor)
        self.assertEqual(
            cliente.get(
                reverse("processos:visualizar_processo", args=[self.processo.numero])
            ).status_code,
            200,
        )
        self.assertEqual(
            cliente.get(
                reverse("avaliacoes:avaliar", args=[self.movimentacao.pk])
            ).status_code,
            200,
        )

    def test_gestao_do_ciclo_continua_em_ciclo_encerrado(self):
        self.mudar_status("Arquivado")
        cliente = self.cliente_logado(self.professor)
        self.assertEqual(
            cliente.get(
                reverse("ciclos:editar_ciclo", args=[self.ciclo.pk])
            ).status_code,
            200,
        )
        grupo = GrupoTrabalho.objects.get(pk=self.grupos["JZ"].pk)
        aluno = Usuario.objects.create_user(
            username="aluno.novo",
            email="aluno.novo@teste.local",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.ALUNO,
            **aceite_termos_teste(),
        )
        resposta = cliente.post(
            reverse("ciclos:adicionar_membro", args=[self.ciclo.pk, grupo.pk]),
            {"usuario_id": aluno.pk},
        )
        self.assertTrue(resposta.json().get("sucesso"))

    def test_rota_de_distribuicao_nao_grava_no_ciclo_encerrado(self):
        self.mudar_status("Arquivado")
        self.autuar_processo(self.processo, ["JZ"])
        self.assertFalse(
            GrupoProcesso.objects.filter(
                processo=self.processo, grupo=self.grupos["JZ"]
            ).exists()
        )
