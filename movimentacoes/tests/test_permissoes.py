from __future__ import annotations

from ciclos.models import CicloSimulacao, GrupoTrabalho
from movimentacoes.permissions import grupo_processo_do_usuario, pode_praticar_movimentacao, tipos_praticaveis
from processos.models import ProcessoJudicial
from usuarios.models import Usuario

from processos.tests.fixtures import CenarioMovimentacoesTestCase


class PapelProcessualTests(CenarioMovimentacoesTestCase):
    """Ponto 1 do mapa: papel processual é lido do vínculo com o processo específico."""

    def test_grupo_papel_errado_nao_pratica_movimentacao_exclusiva(self):
        processo = self.criar_processo_protocolado(autor=self.usuarios["APA"])
        self.autuar_processo(processo, ["APA", "APP"])
        self.assertFalse(pode_praticar_movimentacao(self.usuarios["APA"], processo, self.tipo("Custas Recolhidas")))

    def test_usuario_avaliado_pelo_papel_do_processo_especifico_no_ciclo_certo(self):
        usuario = self.usuarios["APA"]
        processo_a = self.criar_processo_protocolado(autor=usuario)

        ciclo2 = CicloSimulacao.objects.create(
            nome_edicao="Ciclo de Teste 2", coordenador=self.professor,
            semestre=2, ano=2026, status=self.status_andamento,
        )
        grupo_app2 = GrupoTrabalho.objects.create(ciclo=ciclo2, cargo_simulacao=self.cargos["APP"], nome="Grupo APP 2")
        grupo_app2.membros.add(usuario)
        processo_b = ProcessoJudicial.objects.create(
            numero=ProcessoJudicial.gerar_numero_cnj(ano=2026, tr=27, origem=self.comarca.pk),
            ciclo=ciclo2, vara=self.vara, tipo_processo=self.tipo_processo, classe=self.classe,
            status_atual=self.tipo("Protocolo da Petição Inicial").efeito_status,
        )
        processo_b.grupos.add(grupo_app2)

        self.assertEqual(grupo_processo_do_usuario(usuario, processo_a).grupo.cargo_simulacao.cod, "APA")
        self.assertEqual(grupo_processo_do_usuario(usuario, processo_b).grupo.cargo_simulacao.cod, "APP")


class RegraCentralPermissaoTests(CenarioMovimentacoesTestCase):
    """Ponto 4 do mapa: condições 1-3 e 5 (papel, sequência, coordenador/professor)."""

    def test_tipo_nao_autorizado_para_papel_bloqueado(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "JZ"])
        self.assertFalse(pode_praticar_movimentacao(self.usuarios["JZ"], processo, self.tipo("Juntada de Documentos")))

    def test_precondicao_fora_de_ordem_nao_aceita(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP", "JZ"])
        self.assertFalse(pode_praticar_movimentacao(self.usuarios["APP"], processo, self.tipo("Contestação")))
        self.avancar_ate_audiencia_sem_acordo(processo)
        self.assertTrue(pode_praticar_movimentacao(self.usuarios["APP"], processo, self.tipo("Contestação")))

    def test_coordenador_e_professor_nao_praticam(self):
        processo = self.criar_processo_protocolado()
        self.autuar_processo(processo, ["APA", "APP"])
        coordenador = Usuario.objects.create_user(
            username="coord.teste", email="coord.teste@teste.local", password="s3nha-teste",
            tipo_perfil_global=Usuario.TipoPerfilGlobal.COORDENADOR,
        )
        self.assertFalse(pode_praticar_movimentacao(coordenador, processo, self.tipo("Juntada de Documentos")))
        self.assertFalse(pode_praticar_movimentacao(self.professor, processo, self.tipo("Juntada de Documentos")))
        self.assertEqual(tipos_praticaveis(self.professor, processo).count(), 0)
