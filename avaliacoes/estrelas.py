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
NOTA_MIN = 0
NOTA_MAX = ESTRELAS_MAX * PONTOS_POR_ESTRELA


def nota_valida(nota) -> bool:
    """A coluna aceita até 99,99; o que o sistema entende é a faixa 0–10."""
    return NOTA_MIN <= nota <= NOTA_MAX


def estrelas_para_nota(estrelas: int) -> Decimal:
    if not ESTRELAS_MIN <= estrelas <= ESTRELAS_MAX:
        raise ValueError(
            f"Estrelas fora de {ESTRELAS_MIN}–{ESTRELAS_MAX}: {estrelas!r}"
        )
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


def nota_para_meias_estrelas(nota) -> int | float | None:
    """
    Média (ou nota) na escala 0–10 em estrelas com meia estrela: cada ponto vale
    meia estrela. Arredonda uma vez só, do valor bruto, para o ponto inteiro mais
    próximo (meio para cima) e limita a 0–5. Devolve 3 ou 3.5, nunca 3.0.
    """
    if nota is None:
        return None
    pontos = int(Decimal(str(nota)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    pontos = max(NOTA_MIN, min(NOTA_MAX, pontos))
    if pontos % PONTOS_POR_ESTRELA == 0:
        return pontos // PONTOS_POR_ESTRELA
    return pontos / PONTOS_POR_ESTRELA


def faixa_da_estrela(estrelas: int | float | None) -> str:
    """Trio de estado do guia: 4–5 ok, 3 atenção, 0–2 erro, sem nota neutro; a meia estrela fica na faixa de baixo."""
    if estrelas is None:
        return "gray"
    if estrelas >= 4:
        return "ok"
    if estrelas >= 3:
        return "warn"
    return "erro"


def contexto_estrelas(estrelas: int | float | None, *, herda_cor: bool = False) -> dict:
    """Dados de `components/_estrelas.html`, iguais para a tag e para o servidor."""
    meias = round((estrelas or 0) * 2)
    return {
        "valor": estrelas,
        "maximo": ESTRELAS_MAX,
        "itens": [
            "cheia" if meias >= 2 * (i + 1) else "meia" if meias == 2 * i + 1 else "vazia"
            for i in range(ESTRELAS_MAX)
        ],
        "herda_cor": herda_cor,
    }
