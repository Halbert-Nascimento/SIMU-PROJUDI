import re
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse

from ciclos.models import CargoSimulacao
from manual.capitulos import CAPITULOS, NOME_DO_PAPEL, SLUG_LINHA_DO_PROCESSO
from manual.linha_processo import atos_do_papel, montar_linha_do_processo

PASTA_CAPITULOS = Path(settings.BASE_DIR) / "manual" / "templates" / "manual" / "capitulos"
CAPTURAS = Path(settings.BASE_DIR) / "manual-usuario" / "assets"
SLUGS_COM_TEXTO = [c.slug for c in CAPITULOS if c.secoes]


def _fragmento(slug: str) -> str:
    return (PASTA_CAPITULOS / f"{slug}.html").read_text(encoding="utf-8")


class PaginasDoManualTests(TestCase):
    def test_todo_capitulo_abre_sem_login(self):
        for capitulo in CAPITULOS:
            with self.subTest(slug=capitulo.slug):
                resposta = self.client.get(reverse("manual:capitulo", args=[capitulo.slug]))
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, capitulo.titulo)

    def test_capitulo_inexistente_responde_404(self):
        resposta = self.client.get(reverse("manual:capitulo", args=["nao-existe"]))
        self.assertEqual(resposta.status_code, 404)

    def test_raiz_leva_ao_primeiro_capitulo(self):
        resposta = self.client.get(reverse("manual:indice"))
        self.assertRedirects(
            resposta, reverse("manual:capitulo", args=[CAPITULOS[0].slug]),
            fetch_redirect_response=False,
        )

    def test_captura_nao_serve_arquivo_fora_da_pasta(self):
        for tentativa in ("../MANUAL_DO_USUARIO.md", "..%2fMANUAL_DO_USUARIO.md", "../../.env"):
            with self.subTest(tentativa=tentativa):
                resposta = self.client.get(f"/manual/img/{tentativa}")
                self.assertIn(resposta.status_code, (400, 404))

    def test_captura_existente_e_servida(self):
        resposta = self.client.get(reverse("manual:imagem", args=["img_01_cadastro_vazio.png"]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "image/png")


class CardsDaTelaDeLoginTests(TestCase):
    def test_os_seis_cards_levam_a_um_capitulo_que_abre(self):
        pagina = self.client.get(reverse("acesso:login")).content.decode()
        destinos = re.findall(r'<a href="(/manual/[^"]+)"[^>]*class="card-manual', pagina)
        self.assertEqual(len(destinos), 6)
        self.assertNotIn("Em breve", pagina)
        for destino in destinos:
            with self.subTest(destino=destino):
                self.assertEqual(self.client.get(destino).status_code, 200)


class ConteudoGeradoTests(TestCase):
    def test_todo_capitulo_com_texto_tem_fragmento_compilavel(self):
        for slug in SLUGS_COM_TEXTO:
            with self.subTest(slug=slug):
                self.assertTrue((PASTA_CAPITULOS / f"{slug}.html").exists())
                get_template(f"manual/capitulos/{slug}.html")

    def test_link_entre_capitulos_aponta_para_id_que_existe(self):
        ids_por_capitulo = {
            slug: set(re.findall(r'\bid="([^"]+)"', _fragmento(slug)))
            for slug in SLUGS_COM_TEXTO
        }
        padrao = re.compile(r"\{% url 'manual:capitulo' '([a-z-]+)' %\}#([^\"']+)")
        for slug in SLUGS_COM_TEXTO:
            texto = _fragmento(slug)
            for destino, ancora in padrao.findall(texto):
                with self.subTest(origem=slug, destino=destino, ancora=ancora):
                    self.assertIn(ancora, ids_por_capitulo.get(destino, set()))
            for ancora in re.findall(r'href="#([^"]+)"', texto):
                with self.subTest(origem=slug, ancora=ancora):
                    self.assertIn(ancora, ids_por_capitulo[slug])

    def test_toda_imagem_referenciada_existe_na_pasta_de_capturas(self):
        padrao = re.compile(r"\{% url 'manual:imagem' '([^']+)' %\}")
        for slug in SLUGS_COM_TEXTO:
            for nome in padrao.findall(_fragmento(slug)):
                with self.subTest(slug=slug, nome=nome):
                    self.assertTrue((CAPTURAS / nome).exists())

    def test_nao_sobra_emoji_de_aviso_nem_link_para_documento_interno(self):
        for slug in SLUGS_COM_TEXTO:
            texto = _fragmento(slug)
            with self.subTest(slug=slug):
                for simbolo in ("⚠", "ℹ", "🔒"):
                    self.assertNotIn(simbolo, texto)
                self.assertNotIn("DADOS_DE_TESTE", texto)


class LinhaDoProcessoTests(TestCase):
    def test_todo_tipo_do_catalogo_esta_numa_fase_do_fluxo(self):
        fases = montar_linha_do_processo()
        self.assertNotIn("Outros atos", [fase.nome for fase in fases])
        numerados = [a.numero for fase in fases for a in fase.atos if a.numero]
        self.assertEqual(numerados, list(range(1, len(numerados) + 1)))

    def test_pagina_mostra_papel_e_pre_condicao_do_catalogo(self):
        resposta = self.client.get(reverse("manual:capitulo", args=[SLUG_LINHA_DO_PROCESSO]))
        corpo = resposta.content.decode()
        self.assertContains(resposta, "Contestação")
        ato = next(
            a for fase in resposta.context["fases"] for a in fase.atos if a.nome == "Contestação"
        )
        self.assertEqual(ato.papeis, ["APP"])
        self.assertEqual(ato.depende_de, ["Audiência de Conciliação — Sem Acordo"])
        self.assertIn('data-filtro-papel="JZ"', corpo)

    def test_consultas_nao_crescem_com_o_numero_de_atos(self):
        with self.assertNumQueries(6):
            montar_linha_do_processo()
        with self.assertNumQueries(6):
            atos_do_papel("JZ")

    def test_capitulo_de_papel_traz_so_os_atos_do_cargo(self):
        resposta = self.client.get(reverse("manual:capitulo", args=["advogados-polo-passivo"]))
        nomes = [a.nome for fase in resposta.context["atos_do_papel"] for a in fase.atos]
        self.assertIn("Contestação", nomes)
        self.assertNotIn("Emenda Apresentada", nomes)
        self.assertNotIn("Sentença", nomes)
        self.assertContains(resposta, 'id="atos-do-papel"')

    def test_sigla_do_papel_tem_hover_com_o_termo_por_extenso(self):
        corpo = self.client.get(
            reverse("manual:capitulo", args=[SLUG_LINHA_DO_PROCESSO])
        ).content.decode()
        for cod, nome in NOME_DO_PAPEL.items():
            with self.subTest(cod=cod):
                self.assertIn(f'<abbr class="pill gray font-mono" title="{nome}">{cod}</abbr>', corpo)
                self.assertIn(f'data-filtro-papel="{cod}" title="{nome}"', corpo)

    def test_nomes_do_hover_sao_os_mesmos_dos_cargos_do_banco(self):
        banco = dict(CargoSimulacao.objects.values_list("cod", "nome"))
        self.assertEqual({c: banco[c] for c in NOME_DO_PAPEL}, NOME_DO_PAPEL)

    def test_atos_sem_papel_aparecem_como_etapa_futura(self):
        fases = montar_linha_do_processo()
        atos = {a.nome: a for fase in fases for a in fase.atos}
        self.assertFalse(atos["Julgamento pelo Tribunal"].disponivel)
        self.assertIn("Etapa futura", atos["Julgamento pelo Tribunal"].observacao)
        self.assertTrue(atos["Protocolo da Petição Inicial"].disponivel)
        self.assertTrue(atos["Redistribuição"].disponivel)
