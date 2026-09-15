"""
Servidor de arquivos privados que não deixa o navegador renderizar documento
processual como página.

O `DjangoServer` do private_storage delega a `django.views.static.serve`, que
define o Content-Type por `mimetypes.guess_type()` e não manda
`Content-Disposition`. Um arquivo `.html` (ou `.svg`, `.xml`…) gravado no acervo
seria, portanto, executado pelo navegador na mesma origem da aplicação, com a
sessão de quem o abriu — XSS armazenado.

A defesa aqui é de profundidade: mesmo que algum caminho volte a gravar conteúdo
executável, só os tipos comprovadamente inertes são exibidos inline; todo o resto
baixa. A lista espelha as extensões que o `UPLOAD_CONFIG` aceita, mais o `.txt`
em que a peça do editor on-line é gravada.
"""
from __future__ import annotations

import os

from django.http.response import HttpResponseBase
from private_storage.servers import DjangoServer


# Tipos que o navegador exibe sem executar script. Tudo fora daqui baixa.
TIPOS_INLINE = frozenset({
    "application/pdf",
    "image/jpeg",
    "image/png",
    "text/plain",
})


class DocumentoProcessualServer(DjangoServer):
    """Exibe inline só o que é inerte; o resto vai como anexo, com nosniff."""

    @staticmethod
    def serve(private_file):
        response = DjangoServer.serve(private_file)

        # HttpResponseBase, não HttpResponse: django.views.static.serve devolve
        # FileResponse, que desce de StreamingHttpResponse
        if not isinstance(response, HttpResponseBase) or response.status_code != 200:
            return response

        # nosniff: sem ele o navegador pode ignorar o Content-Type declarado e
        # adivinhar o tipo pelo conteúdo, reabrindo o caminho que fechamos acima
        response["X-Content-Type-Options"] = "nosniff"

        tipo = (response.get("Content-Type") or "").split(";")[0].strip().lower()
        if tipo not in TIPOS_INLINE:
            nome = os.path.basename(private_file.relative_name)
            response["Content-Disposition"] = f'attachment; filename="{nome}"'

        return response
