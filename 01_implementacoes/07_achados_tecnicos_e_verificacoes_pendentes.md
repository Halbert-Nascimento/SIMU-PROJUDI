# SIMU-PROJUDI — Achados Técnicos e Verificações Pendentes

**Data:** 20/09/2026
**Origem:** análise das quatro falhas que a suíte completa já tinha na `develop`, descobertas
ao rodar `manage.py test` inteiro durante a etapa 1 do plano de atribuição e redistribuição
de grupos (ver `06_atribuicao_e_redistribuicao_de_grupos.md`).
**Natureza:** **nenhum item aqui é defeito com impacto visível hoje.** São imprecisões de
modelagem, dívidas estruturais e estados latentes. O que justifica registrá-los é que um
deles já produziu um teste errado, e outro decide como a leitura de estado da etapa 2 tem
que ser escrita.

## Como ler cada item

- **Evidência** — arquivo, linha ou saída real que sustenta o achado.
- **Classificação** — imprecisão de modelagem, dívida estrutural, latente, decisão de
  implementação ou qualidade de teste.
- **É defeito hoje?** — com a verificação que respondeu a pergunta.
- **Verificar quando** — o momento em que o item volta a importar.

---

## 1. `GrupoProcesso` carrega dois significados diferentes

Uma única linha de `GrupoProcesso` serve para dois fatos distintos do processo:

| Momento | O que a linha significa |
|---|---|
| protocolo | este grupo peticionou |
| autuação / distribuição | este grupo foi designado para atuar |

A view do cadastro vincula o grupo de quem protocolou com o comentário
*"o vínculo formal ao grupo (e ao polo) só acontece na Autuação"* — ou seja, o código
declara uma distinção que os dados não têm. Como a linha é a mesma, o retrato
`vinculos_existentes` da distribuição não consegue separar uma coisa da outra, e a regra
"só notifica vínculo novo" engole o protocolante na autuação.

**Evidência:** `processos/views.py:147-149` (vínculo do protocolante) e
`processos/views.py:672-684` (retrato dos vínculos e `grupos_novos`).

**Classificação:** imprecisão de modelagem.

**É defeito hoje?** Não. Verificado que o protocolante fica sabendo da autuação por outro
caminho: `notificar_movimentacao_registrada` avisa todos os grupos vinculados, menos o autor
do ato — que é o usuário da serventia. E o grupo conhece o próprio papel por pertencer a ele,
então a informação que a notificação de vínculo carrega ("como Advogados Polo Ativo") não é
novidade para ele.

**O que isso já custou:** dois testes de `processos/tests/test_notificacoes_grupo.py` foram
escritos contra a intenção do comentário em vez do comportamento do código, e falhavam. Quem
os escreveu leu a promessa, não a linha.

**Verificar quando:** se algum dia for preciso distinguir "peticionou" de "foi distribuído"
— por exemplo, para notificar o protocolante na autuação, ou para relatório de distribuição.
Aí a linha precisa de um campo que diga sua origem, e todo lugar que hoje conta vínculos
passa a ter que escolher qual dos dois quer.

---

## 2. O estado "vinculado sem polo" é legítimo antes da autuação

Entre o protocolo e a autuação, o processo fica exatamente assim: o grupo que peticionou tem
`GrupoProcesso`, e o `PoloProcessual.grupo` é nulo. Não é acidente — é asserção explícita da
suíte.

**Evidência:** `processos/tests/test_protocolo_autuacao.py::test_polo_processual_sem_grupo_apos_protocolo`.

**Classificação:** decisão de implementação, com consequência direta na etapa 2 do plano.

**Consequência:** a função que lê o estado das quatro posições da tela nova **tem que ler o
vínculo (`GrupoProcesso`), não o polo (`PoloProcessual.grupo`)**. Escrita a partir do polo, o
grupo que protocolou desapareceria da tela: o serventuário veria "Polo ativo: Pendente" num
processo que já tem advogado e petição inicial nos autos.

A decisão 2.3 do documento 06 diz que atribuir vincula e dá o polo no mesmo ato. O que falta
dizer lá, e fica registrado aqui: existe um estado anterior legítimo em que o vínculo veio sem
o polo, e **confirmar a distribuição é o que o regulariza**.

**Verificar quando:** etapa 2, ao escrever a leitura de estado; e etapa 4, conferindo no
navegador um processo ainda "Protocolado" — a posição do papel de quem protocolou tem que
aparecer ocupada, não pendente.

---

## 3. Qualquer papel protocola, e isso pré-ocupa posições inesperadas

A liberdade de qualquer grupo protocolar é regra deliberada e testada. Combinada com o
vínculo automático do item 1, ela produz três entradas diferentes na tela de atribuição:

| Quem protocolou | Como o processo chega à tela |
|---|---|
| grupo APA ou MP | polo ativo já ocupado |
| grupo APP | polo passivo já ocupado, polo ativo pendente |
| grupo JZ | posição de Juiz ocupada, os dois polos pendentes |
| grupo SC | nenhuma posição visível ocupada (SC fica fora da tela) |

As duas últimas linhas são as que importam: o processo tem petição inicial nos autos e **nenhum
advogado em nenhum polo**.

**Evidência:** `processos/tests/test_protocolo_autuacao.py:29-33` percorre os cinco cargos
protocolando e espera 302 em todos.

**Classificação:** latente de interface.

**É defeito hoje?** Não, porque a tela atual não tem noção de posição — ela lista grupos.

**Verificar quando:** etapa 4. A tela precisa exibir esses dois casos sem parecer defeito, e o
resumo não deve sugerir que uma posição foi "esvaziada" quando ela nunca esteve ocupada.

---

## 4. Grupo vinculado sem polo não pode contestar, e nada explica isso ao aluno

Um grupo APP vinculado ao processo mas sem o polo passivo não tem "Contestação" entre os tipos
praticáveis. A tela de movimentar simplesmente não oferece o ato, sem mensagem alguma.

**Evidência:** medido no banco de desenvolvimento, processo 31
(`0000002-23.2026.8.26.0013`, Autuado), que tem dois grupos APP vinculados:

```text
T3 APP        ocupa polo passivo: True   → pode Contestação: True
T3 APP-fora   ocupa polo passivo: False  → pode Contestação: False
```

A regra está em `movimentacoes/permissions.py:33-38` (`_grupo_ocupa_polo_passivo`), aplicada em
`pode_praticar_movimentacao` e em `tipos_praticaveis`.

**Classificação:** latente de experiência, registrado também em 06 §2.3.

**É defeito hoje?** O estado é inválido e a tela nova o impede de nascer. O que permanece é o
silêncio: quando o estado existir por outro caminho (item 7), o aluno não recebe explicação.

**Verificar quando:** se aparecer relato de aluno que "não encontra a Contestação". A correção
barata seria a tela de movimentar dizer por que o ato não está disponível, em vez de só omiti-lo.

---

## 5. `.first()` sem ordenação decide qual grupo do protocolante entra

O vínculo do protocolante sai de `request.user.grupos_trabalho.filter(ciclo=ciclo).first()`, sem
`order_by`. Com o usuário em dois grupos do mesmo ciclo, qual deles é vinculado fica a critério
da ordem que o banco devolver.

**Evidência:** `processos/views.py:147`. A interface impede o cenário —
`ciclos/views.py:265-267` recusa aluno que já está em outro grupo do ciclo — então só o Django
admin alcança o estado ambíguo.

**Classificação:** latente.

**É defeito hoje?** Não pela interface. Pelo admin, sim, e de forma silenciosa.

**Verificar quando:** se a regra "um aluno, um grupo por ciclo" mudar (monitor que atua em dois
papéis, por exemplo). Aí o `.first()` precisa de critério explícito, e a tela de cadastro
provavelmente precisa perguntar por qual grupo a pessoa está peticionando.

---

## 6. Cargos do app `ciclos` são semeados por migração do app `movimentacoes`

`CargoSimulacao` pertence a `ciclos`, mas quem insere os cinco cargos é a migração de catálogo
de `movimentacoes`, cujo próprio comentário registra que o model nunca teve migração de dados
própria — antes disso os cargos vinham de SQL manual e de scripts de seed.

**Evidência:** `movimentacoes/migrations/0004_popular_catalogo_movimentacao.py`, lista
`CARGOS_FALTANTES`.

**Classificação:** dívida estrutural — dependência na direção errada.

**É defeito hoje?** Não. O `get_or_create` da migração é idempotente e resolve o banco criado
do zero, que era o problema real.

**O que isso já custou:** `ciclos/tests.py` criava o cargo APA com `create()` supondo tabela
vazia, e o `cod` unique estourava `IntegrityError` no `setUpClass` — o que impedia **4 testes de
rodar** e não aparecia como falha deles, mas como erro de classe.

**Verificar quando:** ao escrever qualquer fixture nova que precise de cargo, status de ciclo ou
status de processo. Use `get_or_create`. Se a dívida for paga, o lugar certo é uma migração de
dados em `ciclos` e a remoção de `CARGOS_FALTANTES` da 0004 — mas as duas precisam sair juntas,
ou um banco novo fica sem cargo nenhum.

---

## 7. O admin cria estados que a aplicação recusa

`GrupoProcessoInline` permite vincular dois grupos do mesmo papel ao mesmo processo à mão, que é
o estado que a tela nova valida e recusa no backend.

**Evidência:** `processos/admin.py:77-87`. O processo 31 do banco de desenvolvimento é o
resultado real disso (ou do modal aditivo de hoje, que permite o mesmo).

**Classificação:** latente.

**É defeito hoje?** Não — é o admin, e quem o usa tem acesso total por definição. O registro
serve para lembrar que **validação de tela nunca substitui a defesa no serviço**, que é por isso
que a decisão 2.4 do documento 06 inclui a checagem do estado atual do banco antes de aplicar.

**Verificar quando:** se aparecer processo com posição em conflito depois da limpeza da etapa 6.
O caminho mais provável é o admin, não a aplicação.

---

## 8. Teste que passava por motivo vazio

`test_distribuir_grupo_adicional_notifica_so_o_novo` distribuía primeiro para o grupo que havia
protocolado — ou seja, a primeira distribuição não notificava ninguém, o `delete()` seguinte não
tinha o que apagar, e só a segunda metade do teste media algo. Ele passava, mas metade do
cenário era silêncio.

**Classificação:** qualidade de teste. Corrigido junto com as demais falhas: o protocolo passou
a ser do MP, fora do conjunto distribuído, e as duas metades passaram a medir.

**Verificar quando:** sempre. É o caso concreto do que o CLAUDE.md quer dizer com "verde não é
prova" — o teste estava verde enquanto media a ausência de qualquer coisa.

---

## 9. `verificar.py check` nunca fecha em zero, e por uma sombra só

Origem diferente da dos oito itens acima: apareceu ao rodar a bateria de verificação
durante a correção dos achados da revisão do PR #15, não na análise da etapa 1.

O `check` termina com `check: 1 problema(s)` e sai com código 1 em qualquer execução, na
`develop` e em qualquer branch que saia dela. O problema é sempre o mesmo:

```
raio e sombra
  [SOMBR] templates/static/css/componentes.css: box-shadow: 0 12px 30px -12px rgba(10, 8, 61, .5)
```

É o `.toast`. A lista `SOMBRAS_OK` do verificador conhece exatamente duas sombras — a do
modal (`rgba(10, 8, 61, .45)`) e o halo de validação (`rgba(192, 57, 43, .12)`) — e o toast
usa uma terceira, com alfa `.5` e geometria própria. O verificador não está errado sobre o
fato; ele está reportando que existe no CSS uma sombra que o guia não autorizou.

Vale separar do resto da saída: os 24 `[aviso]` de escala de fonte **não** entram nessa
conta. Avisos não somam problema e não mudam o código de saída — só a sombra soma.

**Evidência:** `templates/static/css/componentes.css:204` (o `.toast`), contra
`scripts/verificar.py:47-49` (a lista `SOMBRAS_OK`). Introduzida em `71804b6`
*"feat: novo design de toast"* (11/09/2026), antes desta linha de trabalho — nenhum commit
de atribuição e redistribuição de grupos tocou nesse arquivo.

**Classificação:** dívida estrutural — de ferramenta, não de tela.

**É defeito hoje?** Não como pixel: o toast renderiza bem, a sombra é discreta e coerente com
a do modal. O defeito é no instrumento. Um `check` que nunca fecha em zero ensina quem o roda
a ler "1 problema(s)" como estado normal, e o próximo `border-radius: 3px` de verdade vai sair
na mesma seção da saída, com a mesma cara, e passar batido. O valor do verificador é poder
confiar que zero significa zero — enquanto o piso for 1, ele não tem esse valor. Foi
exatamente o raciocínio que esta correção precisou fazer para descartar o item como
pré-existente, e é o raciocínio que a próxima vai ter que refazer do zero.

**A decisão pende do guia, que está fora do repositório** (`design/Guia de Design
SIMU-PROJUDI.dc.html` — o diretório `design/` não existe aqui). Duas saídas, e elas se
excluem:

| Se o guia | Então |
|---|---|
| especifica sombra para o toast (seção 07 é onde o modal mora) | a sombra é legítima e falta uma terceira entrada em `SOMBRAS_OK` |
| só admite sombra em modal, como diz o resumo do CLAUDE.md | a sombra do toast sai do CSS, e o flutuante se resolve por borda como o resto do sistema |

O que **não** é saída: relaxar o casamento do verificador ou passar a sombra por um caminho
que ele não lê. Isso apaga o aviso sem resolver a pergunta, e a próxima sombra fora do guia
entra sem ninguém ver.

**Verificar quando:** na próxima vez que alguém abrir o guia por outro motivo — é uma
consulta de trinta segundos à seção 07, e ela fecha o item nos dois sentidos. Até lá, quem
rodar `check` deve tratar `1 problema(s)` como o piso conhecido e conferir se a linha é
**esta**; qualquer outra linha, ou qualquer contagem acima de 1, é regressão nova.
