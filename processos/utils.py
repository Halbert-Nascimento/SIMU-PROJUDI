from __future__ import annotations

import json
import re

from django.conf import settings
from django.http.request import RawPostDataException

# ---------------------------------------------------------------------------
# Constantes lidas do settings.py — altere apenas em UPLOAD_CONFIG
# ---------------------------------------------------------------------------
_cfg = getattr(settings, "UPLOAD_CONFIG", {})

MAX_FILE_SIZE: int = _cfg.get("MAX_FILE_SIZE_MB", 7) * 1024 * 1024
ALLOWED_EXTENSIONS: list[str] = _cfg.get("ALLOWED_EXTENSIONS", [".pdf", ".docx", ".jpg", ".jpeg"])
ALLOWED_MIME_TYPES: list[str] = _cfg.get("ALLOWED_MIME_TYPES", [])
BLOCKED_MIME_PREFIXES: list[str] = _cfg.get("BLOCKED_MIME_PREFIXES", [])


def contexto_upload() -> dict:
    """Limites de upload para os templates, lidos da mesma configuração que valida o arquivo."""
    return {
        "upload_max_mb": _cfg.get("MAX_FILE_SIZE_MB", 7),
        "upload_allowed_extensions_json": json.dumps(ALLOWED_EXTENSIONS),
        "upload_accept_attr": ",".join(ALLOWED_EXTENSIONS),
        "upload_formatos_texto": ", ".join(e.lstrip(".").upper() for e in ALLOWED_EXTENSIONS),
    }


# ---------------------------------------------------------------------------
# Leitura de entrada não confiável
# ---------------------------------------------------------------------------

# 18 dígitos cabem em BIGINT; acima disso o banco responderia com erro
_FORMATO_ID = re.compile(r"[0-9]{1,18}")


def ler_json_objeto(request) -> dict | None:
    """Corpo da requisição como objeto JSON, ou None para qualquer outra coisa."""
    try:
        dados = json.loads(request.body)
    # JSON ou UTF-8 inválido, aninhamento fundo demais, ou formulário no lugar de JSON
    except (ValueError, RecursionError, RawPostDataException):
        return None
    return dados if isinstance(dados, dict) else None


def id_inteiro(valor) -> int | None:
    """Chave primária recebida como inteiro ou texto de dígitos; None se inválida."""
    if isinstance(valor, bool) or not isinstance(valor, (int, str)):
        return None
    texto = str(valor)
    return int(texto) if _FORMATO_ID.fullmatch(texto) else None


def ids_inteiros(valores) -> list[int] | None:
    """Lista de chaves primárias; None se não for lista ou houver item inválido."""
    if not isinstance(valores, list):
        return None
    ids = [id_inteiro(valor) for valor in valores]
    return None if None in ids else ids


# ---------------------------------------------------------------------------
# Exibição de documentos das partes
# ---------------------------------------------------------------------------


def mascarar_cpf_cnpj(documento: str | None) -> str:
    """
    Esconde letras e dígitos, preservando a pontuação digitada:
    CPF vira ***.456.789-** e CNPJ mostra só da 3ª à 8ª posição.
    """
    texto = documento or ""
    total = sum(caractere.isalnum() for caractere in texto)
    # fora de 11 ou 14 posições não há como saber o que é seguro mostrar
    visiveis = {11: range(3, 9), 14: range(2, 8)}.get(total, range(0))
    saida, posicao = [], 0
    for caractere in texto:
        if not caractere.isalnum():
            saida.append(caractere)
            continue
        saida.append(caractere if posicao in visiveis else "*")
        posicao += 1
    return "".join(saida)


# ---------------------------------------------------------------------------
# Validação de arquivo único
# ---------------------------------------------------------------------------

def validar_arquivo(arquivo) -> tuple[bool, str]:
    """
    Retorna (True, "") se o arquivo é válido.
    Retorna (False, mensagem_de_erro) caso contrário.
    Ordem de verificação: tamanho → extensão → MIME real (magic bytes).
    """
    nome = arquivo.name
    max_mb = MAX_FILE_SIZE // (1024 * 1024)

    if arquivo.size > MAX_FILE_SIZE:
        return False, (
            f'O arquivo "{nome}" excede o limite de {max_mb}MB '
            f"({arquivo.size / (1024 * 1024):.1f}MB enviado)."
        )

    ext = f".{nome.rsplit('.', 1)[-1].lower()}" if "." in nome else ""
    if ext not in ALLOWED_EXTENSIONS:
        extensoes = ", ".join(ALLOWED_EXTENSIONS)
        return False, (
            f'O arquivo "{nome}" não corresponde ao formato permitido. '
            f"Formatos aceitos: {extensoes}."
        )

    mime = _detectar_mime(arquivo)

    if any(mime.startswith(prefix) for prefix in BLOCKED_MIME_PREFIXES):
        return False, (
            f'O arquivo "{nome}" foi identificado como executável ou binário '
            f"e não é permitido (tipo detectado: {mime})."
        )

    if ALLOWED_MIME_TYPES and mime not in ALLOWED_MIME_TYPES:
        return False, (
            f'O arquivo "{nome}" possui um tipo de conteúdo não autorizado '
            f"({mime}). Formatos aceitos: {', '.join(ALLOWED_EXTENSIONS)}."
        )

    return True, ""


# ---------------------------------------------------------------------------
# Validação em lote
# ---------------------------------------------------------------------------

def validar_multiplos_arquivos(
    arquivos,
    nomes_personalizados: list[str] | None = None,
) -> tuple[list[tuple], list[str]]:
    """
    Valida uma lista de arquivos.

    Retorna:
        validos  — lista de (arquivo, titulo_final) prontos para persistir
        erros    — lista de strings com mensagens de erro por arquivo rejeitado
    """
    validos: list[tuple] = []
    erros: list[str] = []
    nomes = nomes_personalizados or []

    for i, arquivo in enumerate(arquivos):
        ok, msg = validar_arquivo(arquivo)
        if not ok:
            erros.append(msg)
            continue
        titulo = (
            nomes[i].strip()
            if i < len(nomes) and nomes[i].strip()
            else arquivo.name
        )
        validos.append((arquivo, titulo))

    return validos, erros


# ---------------------------------------------------------------------------
# Detecção de MIME real via magic bytes
# ---------------------------------------------------------------------------

def _detectar_mime(arquivo) -> str:
    """
    Lê os primeiros 2 KB do arquivo para identificar o tipo MIME real.
    Usa python-magic (não confia no nome nem na extensão informados).
    Requer: pip install python-magic-bin (Windows) ou python-magic + libmagic (Linux/Mac).
    """
    import magic  # import tardio — evita falha na importação se o pacote não estiver instalado em outros contextos
    header = arquivo.read(2048)
    arquivo.seek(0)
    return magic.from_buffer(header, mime=True)
