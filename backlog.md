# Backlog — ajustes futuros do simu-projudi

Itens levantados durante a revisão do manual do usuário (outubro/2026). Cada um diz de onde veio e o que falta decidir ou fazer.

---

## A. Decisões do dev (dúvidas sobre o catálogo de movimentações)

### A1. Quem pode abrir (protocolar) um processo?

- **Desenho** (`docs-tuto/Sistema/fluxo_processual_projudi_tabelas.md`, ato nº 1 e nota `*`): só grupos com papel APA ou MP abrem um processo; APP, SC e JZ não.
- **Código:** a view `cadastrar_processo` (`processos/views.py`) só exige login, sem checar cargo. No catálogo, "Protocolo da Petição Inicial" não tem papel autorizado (comentário da migration 0004: "protocolo é livre", revisão de 11/09/2026).
- **Pergunta:** qual regra vale? Se for a do desenho, falta a trava na view; se for a do código, o desenho precisa ser atualizado.
- **Efeito no manual:** hoje o manual não afirma restrição nenhuma. Se a regra mudar, o capítulo do Aluno (seção "Como cadastrar um processo") e os capítulos de APA e MP precisam dizer quem pode.

### A2. Status da Citação por Edital

- **Desenho:** a linha do ato nº 28 mostra o efeito sobre o status como "—".
- **Catálogo:** o ato dá o status "Citado", e a própria lista de status do desenho inclui a Citação por Edital em "Citado".
- **Conclusão:** o catálogo está certo; só a tabela de desenho está inconsistente. Corrigir a linha nº 28 do documento de desenho.

### A3. Réplica do Autor liberada ao APP

- O catálogo autoriza APA, APP e MP. A Réplica é, juridicamente, ato do autor, e o APP representa o réu.
- Diferente da Contestação, a Réplica não tem trava de polo.
- **Pergunta:** foi decisão, ou veio do agrupamento "tipos reativos"? Decidir se a Réplica ganha uma trava de polo ativo.
- Observação: o polo vem do papel (`_POLO_DO_CARGO` em `processos/services.py`: APA ocupa o polo ativo, APP o passivo). Então a trava de polo ativo na Réplica, na prática, excluiria o APP.
- Hoje o manual descreve a situação de forma neutra, como autorregulação dos grupos.

### A4. Trânsito em Julgado com Apelação em curso

- A pré-condição é "o ato já foi registrado alguma vez". Como a Publicação/Intimação já aconteceu antes da Apelação, a Serventia ainda consegue registrar o Trânsito em Julgado com um recurso em andamento.
- **Pergunta:** é limitação conhecida do modelo de pré-condições (o módulo de Prazos não existe), ou deve bloquear?
- O manual avisa que o simulador não confere se houve recurso.

---

## B. Bugs e inconsistências do sistema

### B1. Dica de upload na tela Movimentar

- `movimentacoes/templates/movimentacoes/movimentar_processo.html` (linhas ~181-182) diz "Tamanho máximo: 10MB por arquivo • PDF, DOC, DOCX, ODT, JPG, PNG" e o `accept` do campo aceita `.doc`, `.odt` e `.png`.
- A validação real (`UPLOAD_CONFIG` em `core/settings.py` e `processos/utils.py`) aceita só PDF, DOCX, JPG e JPEG, até 7 MB.
- Corrigir o texto e o `accept` para lerem as mesmas constantes da validação (como já faz o cadastro de processo, via `_upload_ctx`).

### B2. Efeitos de prazo, audiência e notificação são só marcações

- `processar_efeitos_colaterais` (`movimentacoes/services.py`) é um laço vazio. Os módulos de Prazos e de Audiências não existem.
- A notificação real é genérica: toda movimentação avisa os demais grupos vinculados ao processo. A categoria "notifica" do catálogo não faz nada além de exibir um indicador.
- Manual: já descreve como marcação.

### B3. Etapa de 2º grau não implementada (de propósito)

- Julgamento pelo Tribunal, os quatro resultados de recurso e a Baixa dos Autos não têm papel autorizado; "Recurso Superior?" e "REsp/RE" dependem deles e ficam inalcançáveis.
- Está documentado como expansão futura (mapa de implementação, Ponto 3). O desenho prevê um papel "Tribunal / 2º Grau".
- Testes que contornam a regra: `movimentacoes/tests/test_catalogo_tipos.py` (linhas ~77-92) registram esses atos com o usuário do Juiz via `registrar_movimentacao`, que não passa pela checagem de papel. Quando a etapa for implementada, revisar esses testes.

### B4. Menu "Audiências" e "Marcar Audiência"

- Aparecem na interface, mas não estão implementados (o manual marca como "seção em elaboração").

### B5. Verificador de design

- `python scripts/verificar.py check` acusa 1 problema: sombra fora do guia em `templates/static/css/componentes.css` (`box-shadow: 0 12px 30px -12px rgba(10, 8, 61, .5)`). Já existia antes do trabalho do manual.

---

## C. Manual do usuário

- **PDF:** ainda não existe o link de download. O link "Linha do processo" do texto aponta para uma página dinâmica e não funcionará no PDF; decidir como tratar na geração.
- **Seção "Navegação de Arquivo"** (capítulo do Aluno): marcada "em elaboração".
- **Capítulo do Coordenador:** continua curto, só descreve a diferença para o Admin.
- **Links externos "Na vida real"** (Projudi do TJGO, CPC, tabelas do CNJ etc.): descartados por ora; o usuário decide depois se há necessidade.
- **Conferência no navegador:** hover, menu lateral no celular, busca, ampliação das imagens e leitura em 12px.
- **Deploy:** a pasta `manual-usuario/assets` precisa estar na imagem; as capturas são servidas pela rota `/manual/img/`. Antes de subir, rodar `py -3.13 scripts/gerar_manual_html.py --check`.
- **Dev local:** `python manage.py runserver --insecure` serve os estáticos com `DEBUG=False`.
- **Documentos que dependem destas decisões:** `docs-tuto/DUVIDAS_CATALOGO_MOVIMENTACOES.md` (texto enviado ao dev; a dúvida sobre 2º grau já foi respondida).
