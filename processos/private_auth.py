from __future__ import annotations

from movimentacoes.models import DocumentoAnexado

from .permissions import pode_visualizar_processo


def pode_baixar_documento(private_file) -> bool:
    """
    Autorização do `private-media/` (PRIVATE_STORAGE_AUTH_FUNCTION).

    A rota do private_storage casa com qualquer caminho, e a função padrão da
    biblioteca (`allow_authenticated`) só pergunta se há alguém logado. Como o
    caminho é previsível — `processos/{numero_cnj}/{nome_do_arquivo}` — e o
    número CNJ é público, isso entregava qualquer anexo a qualquer sessão,
    inclusive os de processo em segredo de justiça.

    Aqui o arquivo é localizado pelo caminho e passa exatamente pela mesma regra
    que guarda a tela do processo: processo público continua público (decisão de
    projeto), e o segredo de justiça passa a valer também para os arquivos.

    Arquivo sem `DocumentoAnexado` correspondente é negado: não há como saber a
    que processo ele pertence, logo não há como autorizar.
    """
    doc = (
        DocumentoAnexado.objects
        .select_related("movimentacao__processo__ciclo")
        .filter(caminho_arquivo=private_file.relative_name)
        .first()
    )
    if doc is None:
        return False

    return pode_visualizar_processo(
        private_file.request.user,
        doc.movimentacao.processo,
    )
