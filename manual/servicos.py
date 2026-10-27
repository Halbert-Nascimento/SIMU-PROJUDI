from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from .capitulos import CAPITULOS, GRUPO_INICIO, GRUPO_PAPEIS, GRUPO_PERFIS, GRUPO_REFERENCIA, POR_SLUG

ARQUIVO_METADADOS = Path(__file__).resolve().parent / "metadados.json"
ORDEM_GRUPOS = (GRUPO_INICIO, GRUPO_PERFIS, GRUPO_PAPEIS, GRUPO_REFERENCIA)


@cache
def _metadados() -> dict:
    return json.loads(ARQUIVO_METADADOS.read_text(encoding="utf-8"))


def versao_do_manual() -> str:
    # o que vem entre parênteses é nota de bastidor da redação, não informação para o leitor
    return _metadados()["versao"].split(" (")[0]


def atualizado_em() -> str:
    ano, mes, dia = _metadados()["atualizado"].split("-")
    return f"{dia}/{mes}/{ano}"


def sumario_da_pagina(slug: str) -> list[dict]:
    return _metadados()["paginas"].get(slug, {}).get("sumario", [])


def capitulos_por_grupo() -> list[tuple[str, list]]:
    return [
        (grupo, [c for c in CAPITULOS if c.grupo == grupo])
        for grupo in ORDEM_GRUPOS
    ]


def vizinhos(slug: str):
    posicao = [c.slug for c in CAPITULOS].index(slug)
    anterior = CAPITULOS[posicao - 1] if posicao > 0 else None
    seguinte = CAPITULOS[posicao + 1] if posicao < len(CAPITULOS) - 1 else None
    return anterior, seguinte


def capitulo_ou_none(slug: str):
    return POR_SLUG.get(slug)
