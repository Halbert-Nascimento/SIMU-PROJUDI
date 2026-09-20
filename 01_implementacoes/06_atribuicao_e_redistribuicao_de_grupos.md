# SIMU-PROJUDI — Atribuição e Redistribuição de Grupos ao Processo

**Data:** 19/09/2026, revisado em 20/09/2026 (seções 2.3, 11 e 13)
**Status:** aguardando validação — nenhuma linha de código escrita.
**Base:** leitura do código atual nesta data (`processos`, `ciclos`, `movimentacoes`,
`notificacoes`, `avaliacoes`), consulta ao banco de desenvolvimento para conferir estado
legado, e as decisões fechadas na discussão que originou este documento.

**Objetivo:** substituir o fluxo de atribuição de grupos ao processo — hoje um modal
aditivo na lista do serventuário — por uma tela de duas etapas, por processo, onde cada
posição processual tem um grupo só, toda troca deixa evento nos autos, e nada é gravado
antes de o serventuário ver o resumo do que vai acontecer.

---

## 1. O problema hoje

O serventuário atribui grupos por um modal na lista de processos, que fala com o endpoint
JSON `processos:atribuir_grupo_processos` (`processos/views.py:626-723`). Quatro
características desse desenho geram os defeitos que esta implementação resolve:

1. **A operação é aditiva.** `processo.grupos.add(*grupos)` só acrescenta. Nada no caminho
   impede dois grupos do mesmo papel no mesmo processo — e não impediu: o processo 31 do
   banco de desenvolvimento tem `T3 APP` e `T3 APP-fora` vinculados.
2. **A única forma de desvincular é destrutiva.** O card "Remover atribuição"
   (`data-grupo-id=""`) manda `grupo_ids` vazio, e a view apaga *todos* os vínculos dos
   processos selecionados de uma vez (`views.py:717-720`). Não existe desvincular um.
3. **A redistribuição é invisível.** O evento "Autuação e Distribuição" só é registrado
   quando o processo está "Protocolado"; depois disso, trocar de grupo não registra nada,
   não muda status e reatribui polos em silêncio. Quem sai do processo também não é
   notificado — só quem entra.
4. **O polo é sobrescrito às cegas.** A distribuição joga todas as partes do polo ativo do
   processo para o grupo APA, e as do passivo para o APP, com um `update()`
   (`views.py:686-697`). Com dois APA vinculados, o último a entrar rouba o polo do outro
   sem aviso.

---

## 2. Decisões

### 2.1 Uma tela própria, por processo, em vez do modal

`processos/<numero>/grupos/`, renderizada no servidor, irmã da tela "Movimentar Processo".
Duas etapas: matriz de posições e resumo de confirmação.

**Por quê:** o CLAUDE.md fixa o projeto como server-side rendered sem API REST. A tela tem
duas etapas, desfazer por linha e um resumo — no caminho do modal isso tudo seria estado em
JavaScript sem cobertura de teste. Renderizada no servidor, o estado mora no formulário, a
validação mora num `Form` do Django e cada regra vira um `client.post()` de teste.

**Consequência aceita:** o serventuário sai da lista e volta. Mitigado pelo `?next=`, e a
tela ganha em troca uma entrada que o modal não tinha — de dentro do próprio processo, no
dropdown "Opções".

### 2.2 Escopo de um processo por vez; a atribuição em lote sai

Distribuição, redistribuição e remoção surtem efeito apenas no processo aberto.

**Por quê:** a matriz mostra "o grupo vinculado, se houver". Para N processos selecionados,
cada posição pode ter N valores diferentes, o que exigiria um estado "misto" na linha e
transformaria o resumo em mudança × processo — com ações destrutivas desproporcionais ao
clique (um "Remover" tirando o mesmo papel de vinte processos).

**Consequência aceita:** distribuir o mesmo Juiz para muitos processos passa a ser um
processo por vez.

### 2.3 Quatro posições processuais, não uma linha por papel

| Posição | Opções oferecidas | Efeito ao aplicar |
|---|---|---|
| **Polo ativo** | grupos APA e MP do ciclo | vínculo + grupo de todas as partes do polo ativo deste processo |
| **Polo passivo** | grupos APP do ciclo | vínculo + grupo de todas as partes do polo passivo deste processo |
| **Ministério Público** (interveniente) | grupos MP do ciclo | vínculo sem polo |
| **Juiz** | grupos JZ do ciclo | vínculo sem polo |

Posição vazia é **Pendente**; posição sem nenhum grupo daquele cargo no ciclo é
**Indisponível**. Nenhuma é obrigatória.

"Todas as partes" porque `PoloProcessual` é uma linha por parte — a chave é
`(processo, parte, tipo_polo)`. Um processo com dois autores tem duas linhas `Ativo`, e as
duas recebem o grupo escolhido no campo, como o `update()` de hoje já faz
(`views.py:691-693`). Nada atravessa a fronteira do processo aberto: a tela é por processo
(decisão 2.2) e o filtro sempre inclui `processo=processo`.

**Por quê:** só APA e MP são titulares da ação, então quem ocupa o polo ativo é escolha,
não dedução. A alternativa — listar papéis e derivar o polo por precedência (APA ganha de
MP) — esconde uma regra que ninguém lê na tela: vincular um grupo APA por hábito tiraria o
polo do MP em silêncio, e o caso "MP é o autor num ciclo que tem grupo APA" só funcionaria
se alguém deixasse o papel APA pendente de propósito.

**Consequências:**

- Um grupo APA só entra no processo ocupando o polo ativo; não existe APA vinculado sem
  polo. O mesmo vale para APP e o polo passivo. Isso casa com a regra que já existe:
  "Contestação" exige que o grupo ocupe o polo passivo
  (`movimentacoes/permissions.py:33-38`).
- O MP tem um vínculo só, com dois destinos mutuamente exclusivos. Como titular ocupa o
  polo ativo e `_mp_ocupa_polo_ativo` passa a ser verdade, o que desabilita "MP Deve
  Intervir — Sim"; como interveniente fica vinculado sem polo, estado exigido por
  "Manifestação do MP". Escolher num campo trava o outro.
- A tela declara as quatro posições em código, não se constrói sozinha a partir de
  `CargoSimulacao`. Quem pode ocupar polo é conhecimento de domínio, e o catálogo de
  movimentações já amarra papel por código — um cargo novo exigiria mexer nos dois.

#### O estado que isso elimina: o advogado sem posição

Vínculo e polo são coisas separadas no banco — `GrupoProcesso` põe o grupo no processo,
`PoloProcessual.grupo` diz que ele representa uma parte. Um grupo pode ter o primeiro sem o
segundo, e o sistema já produz esse estado.

| | Vínculo | Polo |
|---|---|---|
| entra no processo, vê os autos mesmo sob segredo | sim | — |
| pratica os atos do seu cargo | sim | — |
| recebe notificação, tem movimentação ancorada e corrigível | sim | — |
| representa uma parte | não | sim |
| habilita "Contestação" | não | **sim** |
| marca o MP como titular, desabilitando "MP Deve Intervir — Sim" | não | **sim** |

O polo não dá acesso; ele diz quem representa quem. Só dois lugares no sistema o leem:
`_grupo_ocupa_polo_passivo` e `_mp_ocupa_polo_ativo`.

O processo 31 do banco de desenvolvimento é o caso real. Dois grupos APP vinculados, e o
polo passivo do réu pertence a um só:

```text
T3 APP        ocupa polo passivo: True   → pode Contestação: True
T3 APP-fora   ocupa polo passivo: False  → pode Contestação: False
```

`T3 APP-fora` está no processo, vê tudo, recebe notificação, pode juntar documento — e não
pode contestar, porque `tipos_praticaveis` exclui "Contestação" de quem não ocupa o polo
passivo. Para o aluno é um grupo que abre a tela de movimentar e não encontra o ato
principal dele, sem nenhuma mensagem explicando por quê.

Com o campo da tela sendo "Polo passivo", escolher um grupo ali vincula e dá o polo no mesmo
ato: não existe caminho que crie um sem o outro, e os dois deixam de poder divergir.

Há, porém, um estado anterior em que eles legitimamente não coincidem: entre o protocolo e a
autuação, o grupo que peticionou está vinculado **sem** polo, o que
`test_polo_processual_sem_grupo_apos_protocolo` assegura de propósito. Confirmar a
distribuição é o que regulariza esse estado — ver achado 2 de
`07_achados_tecnicos_e_verificacoes_pendentes.md`.

### 2.4 Um grupo por papel validado no backend, em três camadas

Não é a forma da tela que garante a regra; a tela só a torna natural.

| Invariante | Onde vive |
|---|---|
| grupo existe, é do ciclo **deste** processo, e tem cargo aceito pela posição | `clean_<campo>` do Form |
| o mesmo grupo não ocupa duas posições | `clean()` do Form |
| o grupo que a tela viu ainda é o que está no banco | `clean()` do Form |
| no máximo um vínculo por papel entre APA/APP/MP/JZ **no estado final** | `processos/services.py`, antes de gravar |
| estado atual do banco já inválido | `services` recusa aplicar e a tela pede resolução |

**Por quê a última linha:** o `GrupoProcessoInline` do admin (`processos/admin.py:77-87`)
permite criar vínculo duplicado à mão a qualquer momento, e o dado legado já tem um caso.
Nenhuma camada pode supor que a tela se comportou.

### 2.5 O grupo Serventia fica fora da tela e fora da regra

SC não aparece entre as posições, não é atribuível nem removível, e pode ter mais de um
vínculo no mesmo processo.

**Por quê:** existem ciclos com dois grupos de cartório (ciclos 9 e 16 do banco de
desenvolvimento), e o processo 12 tem os dois vinculados. Não é lixo:
`pode_praticar_movimentacao` passa por `grupo_processo_do_usuario`, que exige o vínculo —
sem ele, o segundo grupo de cartório não movimenta o processo. O vínculo SC continua
nascendo por demanda na autuação (`get_or_create`), e é ele que ancora o evento nos autos.

### 2.6 Toda troca deixa evento nos autos

Regra única, decidida pelo status do processo no momento da confirmação:

| Situação | Evento registrado |
|---|---|
| processo "Protocolado" | **Autuação e Distribuição** — status passa a "Autuado", como hoje |
| processo já autuado | **Redistribuição** — tipo novo |
| nenhuma mudança na confirmação | nenhum evento |

Um evento por confirmação, não um por posição, com a descrição enumerando o que mudou e
nomeando as posições:

> Polo ativo: "Grupo Alfa" substituído por "Grupo Beta". Ministério Público
> (interveniente): "Grupo MP 1" atribuído. Juiz: "Grupo JZ 2" removido.

O autor do evento é o usuário do cartório e o `grupo_processo` é o vínculo SC, como a
autuação já faz. Remover todos os grupos de um processo autuado **não** devolve o status
para "Protocolado" — status é fase processual, não função de vínculo. Confirmação que deixe
o processo sem nenhum grupo não autua, guarda que a view já tem.

#### Refinamento na etapa 3 (20/09/2026)

A regra acima fica valendo, com duas precisões que só apareceram ao escrever a aplicação. A
tabela original é a do caso comum; estas duas linhas fecham as bordas.

**1. Protocolado que termina sem ocupante registra Redistribuição.** "Não autua" deixava
implícito que nada seria registrado, e isso abria um buraco: remover o grupo que protocolou
deixaria o processo sem ninguém e **sem rastro algum nos autos**. A regra completa passa a
ser:

| Situação | Evento |
|---|---|
| Protocolado **e** alguma posição ocupada ao final | Autuação e Distribuição (status → Autuado) |
| Protocolado **sem** nenhuma posição ocupada ao final | Redistribuição (status permanece Protocolado) |
| já autuado | Redistribuição |
| nenhuma mudança | nenhum evento |

**2. O dono de cada polo é reescrito mesmo quando não mudou.** Parece redundante e não é: é
o que regulariza o polo nulo do grupo que protocolou (§2.3 e achado 2 do documento 07).
Atribuir o polo passivo a um processo recém-protocolado também faz o polo ativo passar a
pertencer a quem peticionou, e é isso que a confirmação da distribuição significa.

### 2.7 "Redistribuição" é um tipo transversal sem papéis autorizados

Entra no catálogo por migração de dados, na lista `TRANSVERSAIS`, com papéis `()`, sem
pré-condições, sem efeito de status e sem efeitos colaterais. O nome vai como constante em
`movimentacoes/catalogo.py` e entra em `NOMES_TRANSVERSAIS`.

**Por quê transversal:** `NOMES_TRANSVERSAIS` marca tipo que pode repetir —
`tipos_com_janela_aberta` o exclui e `resolver_movimentacao_origem` o libera de validar
janela. Sem isso, a segunda redistribuição de um processo poderia ser lida como "correção
da primeira".

**Por quê sem papéis:** é o que mantém o tipo fora do combobox de movimentar.
`tipos_praticaveis` filtra por `papeis_autorizados=cargo`, e `pode_praticar_movimentacao`
barra POST forjado (`movimentacoes/views.py:80-81`). O mesmo efeito prático que o "Protocolo
da Petição Inicial" tem por exclusão explícita.

**Efeito colateral bem-vindo:** "Cancelamento / Tornar Sem Efeito" é transversal do SC e
aponta `movimentacao_origem` para qualquer movimentação anterior — então o cartório
consegue tornar sem efeito um registro de redistribuição equivocado.

### 2.8 Quem sai do processo é notificado

Novo `TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO` e
`notificar_grupo_desvinculado_processo()` espelhando a função de vínculo que já existe, com
`try/except` e `logger`, disparada em `transaction.on_commit`.

O link da notificação aponta para a **área do servidor**, não para o processo: os dois
templates de notificação envolvem a linha inteira num `<a href>` sem checar se está vazio,
e o processo pode estar sob segredo de justiça — o aluno recém-desvinculado tomaria 403 ao
clicar.

O grupo que entra continua recebendo a notificação de vínculo, e quem permanece recebe
também a de movimentação registrada, automática dentro de `registrar_movimentacao`.

### 2.9 O vínculo apagado não é recuperável, e isso é aceito

`MovimentacaoProcessual.grupo_processo` é `SET_NULL`. Apagar um vínculo zera a âncora de
todas as movimentações daquele grupo, e revincular não desfaz — o novo `GrupoProcesso` tem
outro pk.

**O que se perde:** só a capacidade daquele grupo de **corrigir** o que ele mesmo escreveu
(`pode_editar_movimentacao` devolve False com âncora nula), e a janela não reabre se ele
voltar ao processo. Para quem saiu, fechar é o comportamento desejado.

**O que não se perde, verificado no código:**

- o histórico continua listado — `visualizar_processo` monta a lista de
  `processo.movimentacoes` sem nenhum filtro por grupo;
- os anexos continuam baixáveis — `pode_baixar_documento` delega para
  `pode_visualizar_processo` (`processos/private_auth.py`), que olha segredo de justiça,
  status e vínculo do usuário, nunca `grupo_processo`;
- as notas continuam atribuídas — `FeedbackProfessor` aponta para a movimentação e a tela
  de avaliação resolve o grupo por `membros=autor`.

**Nota:** desvincular não fecha a leitura para quem saiu. Processo sem segredo de justiça e
já autuado é público por decisão de projeto (`processos/permissions.py:35-47`), inclusive
para anônimo. O desvínculo tira o poder de atuar, não o de ler.

### 2.10 Trava de concorrência

O POST leva, por posição, o grupo que a tela viu. Se algum divergir do banco, nada é
aplicado e a tela volta com o estado atual e o aviso.

**Por quê:** o grupo SC é um grupo de alunos, e dois deles mexendo no mesmo processo na
mesma aula é plausível. Sem a trava, a segunda confirmação desfaz o trabalho da primeira
sem deixar rastro.

### 2.11 Permissão como função pura

`pode_atribuir_grupos(usuario, processo)` nova em `processos/permissions.py`: aluno em grupo
de cargo SC do ciclo do processo, espelhando a cláusula final de `pode_editar_processo`.
Hoje essa regra está solta dentro da view.

Admin, coordenador e professor **não** distribuem: quem pratica ato processual é o papel
simulado, não a autoridade sobre o ciclo — a mesma lógica que o módulo de movimentações já
segue.

### 2.12 Lógica de domínio em `processos/services.py` (novo)

A view fica com validar o form, chamar o service e responder. O app `processos` não tem
`services.py` hoje; a view de atribuição tem quase 100 linhas e receberia mais quatro
regras.

---

## 3. A tela

### 3.1 Onde vive e como se chega

`processos/<numero>/grupos/`, ao lado das rotas que já existem para um processo
(`<numero>/dados/`, `<numero>/partes/alterar/`, `<numero>/movimentar/`), declarada antes de
`<str:numero>/` no `urls.py`. Estrutura visual igual à de "Movimentar Processo":
`nav_secundaria`, breadcrumb, `<h1>`, card de identificação do processo, `fieldset` com
`legend` e marcador de passo.

Duas entradas:

1. **Lista do serventuário** — o botão da coluna Ações deixa de abrir modal e passa a ser
   link, carregando `?next=` para a volta cair na lista.
2. **Dentro do processo** — item "Atribuir Grupos" no dropdown "Opções", ao lado de
   "Modificar Dados" e "Movimentar", visível só para quem passa em `pode_atribuir_grupos()`.

### 3.2 Passo 1 — as posições

```text
» Atribuir Grupos ao Processo                          [Passo 1]

┌─ Processo nº 5012788-42.2026.8.09.0079 ──────────────────────┐
│ 1ª Vara Cível / Goiânia  ·  Procedimento Comum Cível         │
│ João da Silva × Empresa Ré Ltda.              [ok] Autuado   │
└──────────────────────────────────────────────────────────────┘

┌─ POSIÇÕES NO PROCESSO ───────────────────────────────────────┐
│ POLO ATIVO                                                   │
│ Grupo Alfa                         [Substituir]  [Remover]   │
│ ──────────────────────────────────────────────────────────── │
│ POLO PASSIVO                                                 │
│ [warn] Pendente                                 [Atribuir]   │
│ ──────────────────────────────────────────────────────────── │
│ MINISTÉRIO PÚBLICO (interveniente)              ‹ escolhendo │
│   ( ) Grupo MP 1                                             │
│   (•) Grupo MP 2                                [Desfazer]   │
│ ──────────────────────────────────────────────────────────── │
│ JUIZ                                                         │
│ [gray] Nenhum grupo deste papel no ciclo                     │
└──────────────────────────────────────────────────────────────┘

                                [Revisar alterações]  [Cancelar]
```

`Atribuir` e `Substituir` listam **apenas os grupos daquele papel no ciclo**; numa
substituição o grupo atual não entra na lista. A linha alterada mostra o efeito no lugar do
estado (`Grupo Alfa → Grupo Beta`) com um `[Desfazer]` ao lado.

### 3.3 Passo 2 — o resumo

```text
» Atribuir Grupos ao Processo                          [Passo 2]

┌─ ALTERAÇÕES A APLICAR ───────────────────────────────────────┐
│ [warn] Substituição   Polo ativo                             │
│                       Grupo Alfa → Grupo Beta                │
│ [ok]   Atribuição     Ministério Público (interveniente)     │
│                       Grupo MP 2                             │
│ [erro] Remoção        Juiz                                   │
│                       Grupo JZ 1                             │
└──────────────────────────────────────────────────────────────┘

┌─ CONSEQUÊNCIAS ──────────────────────────────────────────────┐
│ Polo ativo passa a ser do Grupo Beta.                        │
│ Grupo Alfa e Grupo JZ 1 deixam de poder corrigir as          │
│ movimentações que registraram neste processo, e isso não     │
│ volta se eles forem revinculados depois.                     │
└──────────────────────────────────────────────────────────────┘

┌─ REGISTRO NOS AUTOS ─────────────────────────────────────────┐
│ Redistribuição                                               │
│ "Polo ativo: Grupo Alfa substituído por Grupo Beta.          │
│  Ministério Público (interveniente): Grupo MP 2 atribuído.   │
│  Juiz: Grupo JZ 1 removido."                                 │
└──────────────────────────────────────────────────────────────┘

                                [Confirmar]  [Voltar e ajustar]
```

Três blocos, e os três importam: as mudanças com a natureza sinalizada nos trios de estado
que o guia já tem, as consequências derivadas (dono de cada polo e a perda da janela de
correção — nomeando a petição inicial quando o grupo removido é o que protocolou), e o texto
literal que vai para os autos, para o serventuário conferir antes de gravar.

Botão primário à esquerda do secundário, conforme a seção 04 do guia.

### 3.4 O ciclo de requisições e onde mora o estado

| Requisição | O que acontece |
|---|---|
| `GET` | monta as posições a partir do banco |
| `POST acao=revisar` | valida o Form e re-renderiza a mesma página no passo 2, com as escolhas em campos ocultos. Nada é gravado |
| `POST acao=confirmar` | aplica na transação, `messages.success`, redirect |

**O estado mora no formulário.** Cada posição é um conjunto de `<input type="radio">` — os
grupos daquele papel, mais "remover" quando há grupo vinculado, mais um "manter" que vem
marcado por padrão. Posição que ninguém tocou chega no POST como "manter", sem ambiguidade.
Um `<input type="hidden">` por posição carrega o grupo que a tela viu, para a trava de
concorrência.

O JavaScript só revela e limpa: `[Atribuir]`/`[Substituir]` desocultam a lista de radios da
linha com `el.hidden`, `[Remover]` marca o radio de remoção, `[Desfazer]` volta para
"manter". Nenhuma cor e nenhuma decisão de estado em JS — armadilhas 3 e 4 da seção de
cascata do CLAUDE.md.

O redirect da confirmação vai para o processo, onde a mensagem de sucesso já aparece como
toast (`visualizar_processo.html:192`), ou para a lista quando o `?next=` veio dela — e
nesse caso `pagina_aluno.html` ganha o include de `base/components/_mensagens.html` que hoje
não tem, sem o qual nenhuma mensagem apareceria ali.

---

## 4. Ordem das operações na confirmação

Dentro de um único `transaction.atomic()`:

1. revalida o estado do banco contra o que a tela viu (trava de concorrência);
2. recusa se o estado atual já violar um-grupo-por-papel;
3. apaga os `GrupoProcesso` que saem, e solta o polo daquele grupo
   (`filter(processo=..., grupo=grupo).update(grupo=None)` — por grupo, não por `tipo_polo`,
   para alcançar qualquer cargo que tenha caído num polo);
4. cria os `GrupoProcesso` que entram;
5. atribui os polos das posições de polo ativo e passivo;
6. garante o vínculo SC do usuário (`get_or_create`) e registra o evento;
7. enfileira as notificações em `transaction.on_commit`.

---

## 5. Dado legado

Consulta ao banco de desenvolvimento nesta data: 56 vínculos, **nenhum** par
(processo, grupo) duplicado, e três casos de papel com mais de um grupo:

| Processo | Papel | Grupos |
|---|---|---|
| 12 | SC | Serventuários, Teste 2 |
| 13 | SC | dois grupos de cartório |
| 31 | APP | T3 APP, T3 APP-fora |

Os dois primeiros são legítimos pela decisão 2.5 e ficam. O terceiro é o defeito que o modal
aditivo permite.

**Tratamento:** migração de dados resolve os duplicados de APA/APP/MP/JZ mantendo o vínculo
que tem movimentações — e o mais antigo em caso de empate ou de nenhum ter —, registrando no
log o que foi apagado. SC não é tocado. A defesa na tela continua, porque o inline do admin
pode recriar o estado a qualquer momento.

---

## 6. O que sai do sistema

- a view `atribuir_grupo_processos` e a rota `api/atribuir-grupo/`;
- o modal `grpModal` com seu CSS de tela e as ~180 linhas de JavaScript;
- o card "Remover atribuição" e todo o `removeMode`;
- a coluna de checkbox, o `selAll`, o contador `selCount` e o botão `bulkAssign`;
- o contexto `grupos_vinculados_por_processo` e seu `json_script`;
- o include de `base/components/_toast.html` em `pagina_aluno.html`, que só existia para o
  modal.

`grupo_ids` vazio deixa de significar "apague tudo" porque a rota deixa de existir. Nenhum
teste da suíte atual envia `grupo_ids: []`.

---

## 7. Arquivos afetados

**Novos**

| Arquivo | Conteúdo |
|---|---|
| `processos/services.py` | estado das posições, planejamento das mudanças, aplicação, atribuição de polo, descrição do evento |
| `processos/templates/processos/atribuir_grupos.html` | a tela, passos 1 e 2 |
| `processos/tests/test_atribuicao_grupos.py` | ver seção 9 |

**Alterados**

| Arquivo | O que muda |
|---|---|
| `processos/views.py` | `atribuir_grupos_processo` entra; `atribuir_grupo_processos` e o contexto de lote de `pagina_aluno` saem |
| `processos/forms.py` | `AtribuicaoGruposForm` — um campo por posição, `clean` com as validações e a trava |
| `processos/urls.py` | rota nova antes de `<str:numero>/`; rota do endpoint sai |
| `processos/permissions.py` | `pode_atribuir_grupos()` |
| `processos/models.py` | `UniqueConstraint(processo, grupo)` em `GrupoProcesso` |
| `processos/templates/processos/pagina_aluno.html` | poda do modal e do lote; botão vira link; `_mensagens` entra |
| `processos/templates/processos/visualizar_processo.html` | item "Atribuir Grupos" no dropdown Opções |
| `movimentacoes/catalogo.py` | `NOME_REDISTRIBUICAO` e entrada em `NOMES_TRANSVERSAIS` |
| `notificacoes/models.py` | `TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO` |
| `notificacoes/services.py` | `notificar_grupo_desvinculado_processo()` |
| `processos/tests/fixtures.py` | o helper `autuar_processo`, por onde quase toda a suíte autua |
| `processos/tests/test_protocolo_autuacao.py` | o único teste que posta o JSON cru |
| `scripts/render_smoke.py` | casos da tela nova em `CASOS` |

---

## 8. Migrações

| App | Operação |
|---|---|
| `movimentacoes` | dados — cria o tipo "Redistribuição" como transversal sem papéis autorizados |
| `notificacoes` | `AlterField` do `choices` de `Notificacao.tipo` |
| `processos` | dados (limpeza dos duplicados de papel) + `AddConstraint` do par (processo, grupo) |

A limpeza e a constraint podem viver no mesmo arquivo; são independentes entre si — a
constraint cobre duplicata exata do par, que hoje não existe no banco, e a limpeza cobre
duplicata de papel, que a constraint não alcança.

**Por que a constraint:** `add()` do Django deduplica com um SELECT, mas duas requisições
simultâneas conseguem inserir a duplicata, e a identidade do vínculo passa a sustentar a
feature inteira.

---

## 9. Testes

**Tela e formulário**

- `GET` monta as quatro posições com estado correto: ocupada, pendente e indisponível;
- SC não aparece entre as posições;
- `POST acao=revisar` não grava nada e traz no resumo as três naturezas e os polos
  resultantes.

**Aplicação**

- vínculos aplicados e polos atribuídos: APA no polo ativo, APP no passivo;
- MP no polo ativo vira dono do polo e `_mp_ocupa_polo_ativo` passa a ser verdade;
- MP interveniente fica vinculado sem polo;
- MP nas duas posições é recusado;
- remoção apaga o vínculo pedido e solta só o polo daquele grupo;
- processo "Protocolado" registra "Autuação e Distribuição" e muda o status; processo autuado
  registra "Redistribuição"; confirmação sem mudança não registra nada;
- descrição do evento nomeia as posições e as três naturezas;
- confirmação que remove tudo não autua e não volta o status.

**Validação e permissão**

- grupo de outro cargo no campo da posição é recusado (POST forjado);
- grupo de outro ciclo é recusado;
- usuário fora de grupo SC é recusado;
- estado do banco já inválido faz a tela recusar aplicar.

**Concorrência**

- grupo mudou no banco entre o passo 1 e a confirmação: nada é aplicado e a tela avisa.

**Regressão do histórico**

- movimentação com âncora nula continua listada em `visualizar_processo`, e
  `pode_baixar_documento` continua True para grupo que permanece no processo.

**Notificações**

- grupo que entra recebe vínculo; grupo que sai recebe desvínculo; quem distribuiu não
  recebe; redistribuir para os mesmos grupos não duplica notificação.

Cada asserção nova passa pelo ritual do CLAUDE.md: reintroduzir o defeito e conferir que ela
fica vermelha, e que o teste chega até ela.

---

## 10. Verificação e perdas esperadas no `diff`

`verificar.py diff` compara, por template, as palavras visíveis e o conjunto de `id`, e sai
com erro se algo desapareceu. Esta implementação **vai** acusar perda, de propósito.

**Dez ids somem de `pagina_aluno.html`:** `bulkAssign`, `grpList`, `grpModal`,
`modalCancel`, `modalClose`, `modalConfirm`, `modalProcClass`, `modalProcNum`, `selAll`,
`selCount`.

**Oito trechos de texto somem:** "Atribuir Grupo ao Processo", "Selecione os grupos
responsáveis", "Remover atribuição", "Processo ficará sem grupo definido", "Confirmar
Atribuição", "Cancelar", "Atribuir grupo aos selecionados", "0 selecionados".

Tudo isso é a tela antiga sendo substituída, e o template novo aparece como `[novo]`, que o
`diff` informa sem contar como perda. O fluxo prático: `snapshot` antes de mexer,
implementar, ler o relatório do `diff` conferindo item por item que toda perda está nesta
lista, e refazer o `snapshot` para virar a nova linha de base.

`render_smoke.py` ganha os casos da tela nova — posições ocupadas, todas pendentes, papel
indisponível, e o passo 2 com as três naturezas.

#### Resultado real, medido na etapa 5

```text
[novo ] processos/templates/processos/atribuir_grupos.html
[TEXTO] pagina_aluno.html: sumiu ['Atribuir', 'grupo', 'aos', 'selecionados', '0',
        'selecionados', 'Processo', '—', '—', 'Selecione', 'os', 'grupos',
        'responsáveis', 'Remover']   (a lista é truncada em 14 itens pelo relator)
[ID   ] pagina_aluno.html: sumiu ['', 'bulkAssign', 'grpList', 'grpModal',
        'modalCancel', 'modalClose', 'modalConfirm', 'modalProcClass',
        'modalProcNum', 'selAll', 'selCount', '{{ g.id }}']
[texto] visualizar_processo.html: entrou ['Atribuir', 'Grupos']
diff: 2 perda(s)
```

São os dez ids previstos mais dois artefatos do próprio verificador: o `_args_de_tags`
procura `id=` em qualquer lugar da linha, então casa também com `data-grupo-id=""` e
`data-grupo-id="{{ g.id }}"` dos cartões do modal. Nenhuma perda além do fluxo antigo.

**O navegador não é opcional:** hover, a lista de grupos que abre, o resumo e o contraste dos
três blocos precisam ser conferidos à mão. O CLAUDE.md registra que o botão "Ver Autos"
passou por todas as verificações automáticas sendo ilegível.

---

## 11. Fora de escopo

- **Prazos e audiências** — `processar_efeitos_colaterais` segue sendo um ponto de conexão
  vazio; nenhum módulo desses existe no sistema.
- **Trocar o grupo de cartório de um processo** — SC não é gerenciado por esta tela.
- **Litisconsórcio no mesmo polo** — dois escritórios defendendo a mesma parte não é
  representável: `PoloProcessual.grupo` é uma FK única por linha de polo.
- **Duas partes do mesmo polo com advogados diferentes** — dois autores, cada um com seu
  grupo. Aqui o modelo de dados *suportaria*, porque a linha de polo é por parte e cada uma
  poderia ter seu grupo; o que não existe é tela que ofereça isso. A escolha do polo ativo
  vale para todas as linhas Ativas de uma vez, como hoje. Decisão explícita: se a simulação
  precisar disso, é uma tela nova — um campo por parte em vez de um por polo — e não um
  remendo neste desenho.
- **Polo "Terceiro"** — continua sem receber grupo, como hoje.
- **Bloquear o inline do admin** — ele segue podendo criar estado inválido; a tela defende, o
  admin não é alterado.
- **Redistribuição por coordenador ou professor** — só o cartório distribui.

---

## 12. Critérios de aceite

- [ ] Nenhuma view existente quebrada; rotas e templates afetados conferidos
- [ ] Permissão via `pode_atribuir_grupos()` em `processos/permissions.py`
- [ ] Nenhum acesso a relacionamento dentro de laço — posições e vínculos resolvidos com
      `select_related` antes de montar a tela
- [ ] Toda entrada validada por `Form`; nada lido direto de `request.POST`
- [ ] Migrações geradas e aplicáveis num banco existente e num banco do zero
- [ ] Nomes seguindo o padrão semântico do projeto
- [ ] Comentário só onde o porquê não é óbvio
- [ ] Guia respeitado: token em vez de hex, escala tipográfica, raio 0, `font-mono` no número
      do processo
- [ ] `verificar.py check` sem problemas; `diff` com exatamente as perdas da seção 10
- [ ] `render_smoke.py` verde com os casos novos
- [ ] Suíte completa verde, incluindo os testes que passam pelo helper `autuar_processo`
- [ ] Tela conferida no navegador: hover, lista que abre, resumo, e a volta pelo `?next=`

---

## 13. Etapas de implementação

Branch: `feat/redistribuicao-grupos-processo`.

A divisão segue **mudança paralela**: o caminho novo nasce inteiro ao lado do antigo, a
chave vira num commit pequeno, e só então o antigo é removido. Nenhuma etapa deixa o
sistema meio-ligado.

O que amarra a ordem é uma dependência só, e ela é decisiva: quase toda a suíte autua
processo pelo helper `autuar_processo` (`processos/tests/fixtures.py`), que hoje bate no
endpoint antigo. Apagar o endpoint antes de a tela existir derruba a suíte inteira.

| # | O que entra | Muda comportamento? |
|---|---|---|
| 1 | catálogo e notificações | não |
| 2 | permissão e leitura de estado | não |
| 3 | escrita no service | não |
| 4 | a tela, ao lado do modal | acrescenta caminho |
| 5 | virar a chave | sim, e só aqui |
| 6 | remoção e consolidação | remove o antigo |

### Etapa 1 — Catálogo e notificações

`NOME_REDISTRIBUICAO` em `movimentacoes/catalogo.py` e a entrada em `NOMES_TRANSVERSAIS`;
migração de dados criando o tipo sem papéis autorizados; `TipoNotificacao.GRUPO_DESVINCULADO_PROCESSO`
com a migração de `choices`; `notificar_grupo_desvinculado_processo()`.

Nada chama nada disso. Um tipo sem papéis autorizados é invisível na interface, e as funções
que consultam `NOMES_TRANSVERSAIS` nunca recebem esse tipo. A migração de dados sai com
`reverse_code` que apaga o tipo, para o revert ser limpo.

**Verificação:** `test movimentacoes notificacoes`; `migrate` para frente e para trás.
**Commit:** `feat(movimentacoes): adicionar tipo Redistribuição e notificação de desvínculo de grupo`

### Etapa 2 — Permissão e leitura

`pode_atribuir_grupos()` em `processos/permissions.py` e o `processos/services.py` novo só
com o que lê e planeja: estado das quatro posições, planejamento das mudanças, descrição do
evento, e detecção de papel com mais de um grupo. Funções puras, chamadas por ninguém.

A leitura das posições parte do **vínculo** (`GrupoProcesso`), nunca do polo: processo ainda
"Protocolado" tem o grupo que peticionou vinculado sem polo, e ler pelo polo o faria
desaparecer da tela. Ver achado 2 de `07_achados_tecnicos_e_verificacoes_pendentes.md`.

**Verificação:** `test processos`.
**Commit:** `feat(processos): ler estado das posições do processo e planejar alterações de grupo`

### Etapa 3 — Escrita no service

O `aplicar_*`: apaga vínculo, solta polo, cria vínculo, atribui polo, registra o evento,
enfileira notificação. Exercitado só pelos testes; nenhuma view chama.

**Verificação:** `test processos`, com Protocolado virando autuação e autuado virando
redistribuição.
**Commit:** `feat(processos): aplicar distribuição e redistribuição de grupos com registro nos autos`

### Etapa 4 — A tela, ao lado do modal

`AtribuicaoGruposForm`, a view de três requisições, o template dos dois passos, a rota antes
de `<str:numero>/`, o JS de visibilidade, e a entrada pelo dropdown "Opções" do processo.
**O modal e o endpoint continuam vivos e funcionando.**

É o commit maior e o único momento com dois caminhos para a mesma coisa — de propósito: se a
tela estiver errada, o fluxo antigo segue atendendo.

**`verificar.py snapshot` roda antes desta etapa**, que é a primeira a tocar template.

**Verificação:** `test processos`, `render_smoke`, `verificar check`, e o navegador na URL
nova.
**Commit:** `feat(processos): adicionar tela de atribuição e redistribuição de grupos`

### Etapa 5 — Virar a chave

O botão da lista passa a linkar a tela com `?next=`; o helper `autuar_processo` passa a bater
na tela nova; o teste do JSON cru é reescrito; o include de `_mensagens` entra em
`pagina_aluno`. O endpoint antigo ainda existe, mas ninguém mais o alcança — nem a
interface, nem os testes.

Commit pequeno de propósito: é o único que muda o que o usuário vê, e revertê-lo devolve o
modal sem desfazer nada do que foi construído. É também o único com risco de suíte vermelha,
porque é onde o helper troca de destino — isolado assim, o bisect é trivial.

**Verificação:** suíte completa; navegador pelos dois caminhos de entrada.
**Commit:** `refactor(processos): apontar lista e testes para a tela de atribuição de grupos`

### Etapa 6 — Remoção e consolidação

Saem a view e a rota antigas, o modal, o JS, o CSS de tela, a coluna de checkbox com o lote,
o `grupos_vinculados_por_processo` e o toast. Entram a `UniqueConstraint(processo, grupo)` e
a migração de limpeza dos duplicados de papel.

A limpeza fica melhor aqui: depois da etapa 5 nenhum caminho cria duplicata nova, então ela
roda uma vez e o assunto morre.

**Verificação:** suíte completa, `check`, `diff` conferindo item por item as dez ids e oito
textos da seção 10, `render_smoke`, e `snapshot` novo como linha de base.
**Commit:** `refactor(processos): remover modal e endpoint de atribuição em lote de grupos`

### Atritos que sobram

- **A etapa 4 duplica caminho** — inevitável na mudança paralela, e é o que garante que
  nenhum commit fica sem um fluxo funcionando.
- **A migração de limpeza não é reversível**: ela apaga vínculo, e `git revert` não recria.
  Vai logar o que apagou, e pede um dump do banco de desenvolvimento antes de rodar.
- **Entre as etapas 4 e 6, o processo 31 abre a tela em estado de conflito** (dois APP). A
  tela resolve pedindo qual grupo fica — é o comportamento projetado, só acontecendo antes
  da limpeza.
