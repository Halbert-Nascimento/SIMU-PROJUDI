# Dependências de terceiros

Inventário das dependências do SIMU-PROJUDI. É a **fonte de verdade** do projeto sobre versões e
licenças de terceiros. Última conferência: **26/11/2026**.

> Este arquivo informa; **não é parecer jurídico**. As situações abaixo servem para saber o que
> analisar antes de um eventual produto comercial.

## Como manter

- Dependência nova, atualizada ou removida **atualiza a linha no mesmo commit**.
- Arquivo de CDN novo ou trocado também entra no [histórico](#histórico-dos-arquivos-de-cdn).
- Versão e licença são conferidas na fonte (metadados do pacote ou página oficial), nunca de
  memória. O que não for confirmado fica como `não verificado` ou `a confirmar`.

## Legenda

**Situação comercial**

| Valor | Significado |
|---|---|
| `livre` | Licença permissiva; basta preservar avisos de autoria e licença |
| `com obrigações` | Exige atribuição ou impõe condições além de preservar o aviso |
| `revisar` | Copyleft, licença dupla (livre ou comercial) ou licença não confirmada |

**Criticidade** (o que analisar primeiro)

| Valor | Critério |
|---|---|
| Alta | O sistema não funciona sem ela, ou a troca exige reescrever partes importantes |
| Média | Afeta uma função ou o visual; há substituto com esforço moderado |
| Baixa | Apoio, desenvolvimento ou item fácil de trocar |

## Atenção primeiro

| Nome | Por quê |
|---|---|
| mysqlclient | GPL-2.0-or-later, ligada ao funcionamento do banco |
| TinyMCE e tinymce-i18n | Componente central do editor; a licença muda entre as séries, e deve ser reconferida na fonte a cada atualização |
| MySQL Server | Distribuído sob GPL, com oferta comercial à parte |
| Tailwind (Play CDN) | Licença permissiva, mas a própria documentação o declara só para desenvolvimento |

## Aplicação (Python, execução)

Versões do ambiente de desenvolvimento. As do servidor de produção são definidas pelo
`Dockerfile`, que não está versionado: **a confirmar**.

| Nome | Versão | Licença | Uso no sistema | Situação comercial | Fonte | Criticidade | Plano de substituição |
|---|---|---|---|---|---|---|---|
| CPython | 3.13.2 (local); produção a confirmar | PSF License 2 | Linguagem de execução | livre | https://docs.python.org/3/license.html | Alta | Sem substituição prevista |
| Django | 6.0.3 (faixa `>=6.0,<6.1`) | BSD-3-Clause | Framework web | livre | metadados e `LICENSE` do pacote | Alta | Sem substituição prevista |
| mysqlclient | 2.2.8 | GPL-2.0-or-later | Driver do MySQL | revisar | metadados e `LICENSE` (GPL v2) do pacote | Alta | PyMySQL (ver linha própria) ou o conector oficial, conferindo cada licença antes |
| MariaDB Connector/C (embutido no mysqlclient para Windows) | 3.4.8 | LGPL 2.1 | Biblioteca cliente dentro do binário do Windows | revisar | inspeção do binário e https://github.com/mariadb-corporation/mariadb-connector-c/blob/3.4/COPYING.LIB | Média | Acompanha o mysqlclient |
| PyMySQL | não instalado no ambiente local; produção a confirmar | MIT (versão 1.2.4 no PyPI) | `core/__init__.py` passa a usá-lo no lugar do mysqlclient se estiver instalado | livre | https://pypi.org/pypi/PyMySQL/json | Média | mysqlclient |
| django-private-storage | 3.1.3 | Apache-2.0 | Anexos processuais com autorização | livre | `LICENSE` do pacote (o campo de metadados é malformado) | Alta | View própria de download sobre o armazenamento do Django |
| django-environ | 0.13.0 | MIT (declarada nos metadados) | Leitura do `.env` | livre | metadados do pacote | Média | `os.environ` com leitura própria |
| python-magic-bin | 0.4.14 | MIT; traz `libmagic.dll` | Tipo real do arquivo enviado (Windows) | livre | metadados do pacote; licença da `libmagic` embarcada: ver `libmagic` | Média | `python-magic` com `libmagic` do sistema (já usado no Linux) |
| asgiref | 3.11.1 | BSD-3-Clause | Exigido pelo Django | livre | metadados do pacote | Média | Acompanha o Django |
| sqlparse | 0.5.5 | BSD | Exigido pelo Django | livre | metadados do pacote | Média | Acompanha o Django |
| tzdata | 2025.3 | Apache-2.0 | Fusos horários no Windows | livre | metadados e `LICENSE` do pacote | Baixa | Acompanha o Django |
| python-dotenv | 1.2.2 | BSD-3-Clause | Instalado no ambiente local; nenhum pacote o declara | livre | metadados do pacote | Baixa | Remover se confirmado sem uso |

## Navegador (arquivos de CDN)

| Nome | Versão | Licença | Uso no sistema | Situação comercial | Fonte | Criticidade | Plano de substituição |
|---|---|---|---|---|---|---|---|
| TinyMCE | 8.11.0 | GPL v2 ou posterior, ou licença comercial (`license_key: 'gpl'` no código) | Editor de peças processuais | revisar | https://github.com/tinymce/tinymce/blob/main/LICENSE.md e https://www.tiny.cloud/docs/tinymce/8/license-key/ | Alta | Licença comercial do fabricante ou editor de licença permissiva |
| tinymce-i18n | 26.11.2 | Segue os termos do TinyMCE (`SEE LICENSE IN LICENSE.md`) | Idioma português do editor | revisar | https://registry.npmjs.org/tinymce-i18n/26.11.2 | Média | Acompanha o TinyMCE |
| Tailwind CSS (Play CDN) | sem versão fixa; em 26/11/2026 entregava 3.4.17 | MIT | Toda a pele da interface | livre | https://registry.npmjs.org/tailwindcss e https://tailwindcss.com/docs/installation/play-cdn | Alta | Compilar o CSS no build e servir localmente (`backlog.md`, E2) |
| Font Awesome Free | 6.4.0 | Ícones CC BY 4.0; fontes SIL OFL 1.1; código MIT | Ícones da interface | com obrigações (atribuição) | https://registry.npmjs.org/@fortawesome/fontawesome-free/6.4.0 | Média | Conjunto próprio de SVG ou outra biblioteca de licença permissiva |
| Barlow (Google Fonts) | não versionada | SIL OFL 1.1 | Fonte da interface | com obrigações (OFL) | https://github.com/google/fonts/blob/main/ofl/barlow/OFL.txt | Baixa | Servir localmente com o arquivo de licença |
| Lato (Google Fonts) | não versionada | SIL OFL 1.1 | Fonte de dados codificados | com obrigações (OFL) | https://github.com/google/fonts/blob/main/ofl/lato/OFL.txt | Baixa | Servir localmente com o arquivo de licença |

## Infraestrutura

| Nome | Versão | Licença | Uso no sistema | Situação comercial | Fonte | Criticidade | Plano de substituição |
|---|---|---|---|---|---|---|---|
| MySQL Community Server | série 8.0 em produção (patch a confirmar); 8.4 local | GPL (versão da GPL não verificada) | Banco de dados | revisar | https://www.mysql.com/products/community/ | Alta | Avaliar MariaDB ou PostgreSQL (há migrações específicas de MySQL) |
| nginx | a confirmar | Texto estilo BSD de duas cláusulas | Proxy reverso e HTTPS | livre | https://nginx.org/LICENSE | Média | Outro proxy reverso |
| Gunicorn | a confirmar | MIT | Servidor de aplicação em produção | livre | https://pypi.org/pypi/gunicorn/json | Média | uWSGI ou outro servidor WSGI/ASGI |
| python-magic | a confirmar | MIT | Tipo real do arquivo enviado (Linux) | livre | https://pypi.org/pypi/python-magic/json | Média | Outra detecção por assinatura |
| libmagic (projeto `file`) | a confirmar | Texto estilo BSD de duas cláusulas; pacote da distribuição não conferido | Base do python-magic | livre | https://github.com/file/file/blob/master/COPYING | Média | Acompanha o python-magic |
| Certbot | a confirmar | Apache-2.0 | Certificado TLS | livre | https://pypi.org/pypi/certbot/json | Baixa | Outro cliente ACME |
| Imagens Docker (`python`, `nginx`) e Docker | a confirmar | não verificado | Empacotamento e execução | revisar | `Dockerfile` do servidor (não versionado) | Média | A definir após a conferência |

O painel `/admin/` do Django serve bibliotecas embutidas (jQuery, select2 e XRegExp), que
acompanham o Django; licenças próprias não verificadas.

## Desenvolvimento e testes

Não são distribuídos com a aplicação.

| Nome | Versão | Licença | Uso no sistema | Situação comercial | Fonte | Criticidade | Plano de substituição |
|---|---|---|---|---|---|---|---|
| pytest | 9.2.0 | MIT | Testes | livre | metadados do pacote | Baixa | `manage.py test` |
| pytest-django | 4.14.0 | BSD-3-Clause | Testes | livre | metadados do pacote | Baixa | `manage.py test` |
| black | 26.10.1 | MIT | Formatação | livre | metadados do pacote | Baixa | `ruff format` |
| ruff | 0.17.6 | MIT | Lint | livre | metadados do pacote | Baixa | Outro verificador |
| markdown-it-py | 4.3.0 | MIT | Gera o manual em HTML | livre | metadados do pacote | Baixa | Outra biblioteca Markdown |
| mdurl | 0.1.2 | MIT | Exigido pelo markdown-it-py | livre | metadados do pacote | Baixa | Acompanha o markdown-it-py |
| pathspec | 1.1.1 | MPL 2.0 | Exigido pelo black | com obrigações (MPL) | metadados do pacote | Baixa | Acompanha o black |
| click | 8.5.1 | BSD-3-Clause | Exigido pelo black | livre | metadados do pacote | Baixa | Acompanha o black |
| colorama | 0.4.6 | BSD | Exigido pelo pytest no Windows | livre | metadados do pacote | Baixa | Acompanha o pytest |
| mypy_extensions | 1.2.0 | MIT | Exigido pelo black | livre | metadados do pacote | Baixa | Acompanha o black |
| packaging | 26.4 | Apache-2.0 ou BSD-2-Clause | Exigido por black e pytest | livre | metadados do pacote | Baixa | Acompanha black e pytest |
| platformdirs | 4.14.8 | MIT | Exigido pelo black | livre | metadados do pacote | Baixa | Acompanha o black |
| pytokens | 0.4.1 | MIT | Exigido pelo black | livre | metadados do pacote | Baixa | Acompanha o black |
| iniconfig | 2.3.1 | MIT | Exigido pelo pytest | livre | metadados do pacote | Baixa | Acompanha o pytest |
| pluggy | 1.7.0 | MIT | Exigido pelo pytest | livre | metadados do pacote | Baixa | Acompanha o pytest |
| Pygments | 2.21.0 | BSD-2-Clause | Exigido pelo pytest | livre | metadados do pacote | Baixa | Acompanha o pytest |
| hatchling | usado só na montagem do pacote (versão não fixada) | MIT | `build-system` do `pyproject.toml` | livre | https://pypi.org/pypi/hatchling/json | Baixa | Outro construtor de pacotes |
| pip-audit | 2.10.1 (executado com `uvx`, fora do ambiente do projeto) | Apache-2.0 | Auditoria de vulnerabilidades das dependências | livre | https://pypi.org/pypi/pip-audit/json | Baixa | Outro auditor de dependências |
| uv | 0.10.9 (local) | MIT ou Apache-2.0 | Gerencia o ambiente virtual | livre | https://pypi.org/pypi/uv/json | Baixa | `pip` e `venv` |
| ipython | declarado no extra `dev`; não instalado | não verificado | Console interativo | revisar | `pyproject.toml` | Baixa | Console padrão do Python |
| Node.js | não fixada | não verificado | Executa `scripts/*.mjs` | revisar | ambiente local | Baixa | Outro executor de JavaScript |

## Histórico dos arquivos de CDN

Responde "qual versão estava no ar em cada período". O hash é o SHA-384 do arquivo baixado em
26/11/2026; registrá-lo **não** ativa `integrity` nos templates. "Em produção" deve ser
preenchido a cada deploy.

| Arquivo (URL exata) | Versão | No código desde | Até | Em produção | SHA-384 |
|---|---|---|---|---|---|
| https://cdnjs.cloudflare.com/ajax/libs/tinymce/8.11.0/tinymce.min.js | 8.11.0 | 26/11/2026 | em uso | a preencher no deploy | `sha384-J2h73vI7pLZLVqNaLK1ytglH4uMqLVuGN0FYBkjosER5/naP1IwlTVm+cHrQHO79` |
| https://cdn.jsdelivr.net/npm/tinymce-i18n@26.11.2/langs8/pt-BR.js | 26.11.2 | 26/11/2026 | em uso | a preencher no deploy | `sha384-xv0Hu1//6Oj+Uj9/8Z9wknFcu5m/i8aCPGSf5ZVXZ3LUCWb8aTM0qVAS/3B8Sfc2` |
| https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css | 6.4.0 | 12/03/2026 (`5f3e950`) | em uso | a preencher no deploy | `sha384-iw3OoTErCYJJB9mCa8LNS2hbsQ7M3C0EpIsO/H5+EGAkPGc6rk+V8i04oW/K5xq0` |
| https://cdn.tailwindcss.com (redirecionava para `/3.4.17`) | sem versão fixa | 12/03/2026 (`5f3e950`) | em uso | a preencher no deploy | `sha384-igm5BeiBt36UU4gqwWS7imYmelpTsZlQ45FZf+XBn9MuJbn4nQr7yx1yFydocC/K` (conteúdo de 26/11/2026; pode mudar) |
| https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Lato:wght@400;700;900&display=swap | não versionada | 09/09/2026 (`95736d3`) | em uso | a preencher no deploy | não se aplica (o conteúdo varia por navegador) |

O editor carrega ainda, a partir do mesmo endereço do TinyMCE, os próprios plugins, temas e
folhas de estilo.

### Versões anteriores

| Arquivo (URL exata) | Versão | No código desde | Até | Em produção | SHA-384 |
|---|---|---|---|---|---|
| https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.8.3/tinymce.min.js | 6.8.3 | 21/05/2026 (`f0cfa5d`) | 26/11/2026 | a preencher no deploy | `sha384-1Miaw0hyo/w0cd9ZHUnc7Z8ACgtO+lphAEziGNW4z2C1h3nJfMVVEWA5MI031P+X` |
| https://cdn.jsdelivr.net/npm/tinymce-i18n@23.10.9/langs6/pt_BR.js | 23.10.9 | 21/05/2026 (`f0cfa5d`) | 26/11/2026 | a preencher no deploy | `sha384-xesuNJWp0/+0EWNuEIz9UuwG9JDDpxhwIw4fK2D0nUJx6qQUTaJm4NxkAL8gLvZo` |
| https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css | 6.5.0 (conviveu com a 6.4.0) | 18/03/2026 (`d283105`) | 14/04/2026 (`809ac43`) | não verificado | `sha384-/o6I2CkkWC//PSjvWC/eYN7l3xM3tJm8ZzVkCOfp//W05QcE3mlGskpoHB6XqI+B` |
| https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap | não versionada (IBM Plex Mono, SIL OFL 1.1) | 03/09/2026 (`c51ff3f`) | 09/09/2026 (`95736d3`) | não verificado | não se aplica |

## Registro de licenciamento do TinyMCE (26/11/2026)

- [x] Usado sem modificação do código do editor.
- [x] Carregado por CDN, sem cópia no repositório.
- [x] Atualização de 6.8.3 para 8.11.0 motivada por correção de vulnerabilidades.
- [x] Licença registrada conforme a documentação oficial da versão adotada (linha da tabela).
- [ ] **Pendente:** revisão jurídica antes de eventual produto comercial. A documentação do
      fabricante diz que, em ambiente auto-hospedado para uso comercial, é exigido o complemento
      de gerenciamento de chave de licença comercial; se esse uso cabe no modo `gpl` depende
      dessa revisão.

## Pendências para produto comercial

- [ ] Revisão jurídica do conjunto, começando pelos itens `revisar`.
- [ ] Decidir sobre o mysqlclient (GPL) e o MySQL Server.
- [ ] Decidir sobre a licença do TinyMCE na versão em uso, frente à licença do projeto
      (PolyForm Strict).
- [ ] Publicar os créditos exigidos (Font Awesome, fontes).
- [ ] Confirmar as versões do servidor de produção e das imagens Docker.
- [ ] Substituir o Play CDN do Tailwind.
