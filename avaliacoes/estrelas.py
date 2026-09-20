"""
Avaliação em estrelas sobre a coluna `FeedbackProfessor.nota`.

A coluna continua na escala 0–10: cada estrela vale PONTOS_POR_ESTRELA pontos
(1★ = 2, 5★ = 10). Assim as notas já gravadas seguem válidas, `Avg`/`Max` seguem
funcionando e nenhum dado nem tabela muda. Toda conversão entre as duas escalas
passa por aqui — nenhum outro ponto do sistema deve dividir ou multiplicar por 2.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

ESTRELAS_MIN = 1
ESTRELAS_MAX = 5
PONTOS_POR_ESTRELA = 2


def estrelas_para_nota(estrelas: int) -> Decimal:
    if not ESTRELAS_MIN <= estrelas <= ESTRELAS_MAX:
        raise ValueError(f"Estrelas fora de {ESTRELAS_MIN}–{ESTRELAS_MAX}: {estrelas!r}")
    return Decimal(estrelas * PONTOS_POR_ESTRELA).quantize(Decimal("0.01"))


def nota_para_estrelas(nota) -> int | None:
    """
    Estrelas inteiras de uma nota gravada. Nota antiga que não é múltipla de 2
    (7,35) sobe ou desce para a estrela mais próxima, com meio ponto para cima;
    o valor no banco não é tocado.
    """
    if nota is None:
        return None
    estrelas = (Decimal(str(nota)) / PONTOS_POR_ESTRELA).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP,
    )
    return max(0, min(ESTRELAS_MAX, int(estrelas)))


def media_em_estrelas(media) -> float | None:
    """Média de notas gravadas em estrelas, com uma casa (a média do aluno pode ser 3,9)."""
    if media is None:
        return None
    return round(float(media) / PONTOS_POR_ESTRELA, 1)


def faixa_da_estrela(estrelas: int | None) -> str:
    """Um dos quatro trios de estado do guia: 4–5 ok, 3 atenção, 1–2 erro, sem nota neutro."""
    if estrelas is None:
        return "gray"
    if estrelas >= 4:
        return "ok"
    if estrelas == 3:
        return "warn"
    return "erro"


def contexto_estrelas(estrelas: int | None, *, herda_cor: bool = False) -> dict:
    """Dados do template `components/_estrelas.html` — o mesmo para a tag e para quem renderiza no servidor."""
    return {
        "valor": estrelas,
        "maximo": ESTRELAS_MAX,
        "itens": [i < (estrelas or 0) for i in range(ESTRELAS_MAX)],
        "herda_cor": herda_cor,
    }
