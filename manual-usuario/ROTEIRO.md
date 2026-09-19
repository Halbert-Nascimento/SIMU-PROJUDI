# Roteiro de Execução — Manual do Usuário do simu-projudi

> **Este documento é um "work order" autocontido.** Foi escrito para ser aberto por qualquer
> sessão Claude (ex.: Claude Desktop) que **não tenha o histórico da conversa em que este roteiro
> foi produzido** e que **não carregue o `CLAUDE.md`** deste projeto. Por isso, toda regra
> relevante — inclusive as de conduta geral — está repetida aqui por extenso. Nenhuma decisão
> deste roteiro deve ser lida como "conforme combinado"; cada uma vem com a razão por trás.
>
> **Este arquivo e a pasta `manual-usuario/` ficam na raiz do repositório e SÃO versionados no
> git** (branch `docs/manuais` — usada de forma genérica para este e outros manuais do projeto).
> Isso é diferente de `docs-tuto/` — aquela pasta está
> inteira no `.gitignore` e não é compartilhada por clone; `manual-usuario/` foi movida para fora
> dela exatamente para que qualquer colega que clonar o repositório e mudar para esta branch tenha
> acesso ao roteiro e ao manual.

---

## 0. Cabeçalho de execução

**Objetivo deste documento:** orientar, com regras de conduta e uma sequência de passos
verificável, a produção do Manual do Usuário Final do simu-projudi — um guia passo a passo, tela
por tela, de cada ação que cada perfil de usuário pode realizar no sistema.

**Quem executa:** qualquer sessão Claude com acesso de leitura ao repositório local do projeto
**simu-projudi**, aberto como diretório de trabalho. **Não presuma um caminho absoluto de
máquina** — o repositório pode estar clonado em qualquer pasta, em qualquer sistema operacional
(o autor original usa Windows, `C:\Users\halbe\Programacao\simu-projudi`; um colega de equipe pode
ter clonado em `/home/nome/projetos/simu-projudi` ou em outra letra de unidade/pasta no Windows
dele). Todos os caminhos de arquivo citados neste roteiro (ex.: `acesso/permissions.py`) são
**relativos à raiz do repositório** — identifique a raiz pela presença do `manage.py` e da pasta
`docs-tuto/` nela, não por um caminho fixo.

**Pré-requisito de ferramentas:** este roteiro pressupõe que o executor consegue ler arquivos do
repositório (código Python, templates HTML, `models.py`, etc.) para verificar cada afirmação antes
de escrevê-la no manual. **Se o ambiente em que este roteiro for aberto não tiver esse acesso de
leitura ao repositório, a primeira ação do executor deve ser avisar o usuário disso e pedir que ele
cole o conteúdo dos arquivos necessários — nunca inventar ou supor o comportamento do sistema.**

**Regra geral de conduta (vale para todo o trabalho, do início ao fim):**
Sempre que houver dúvida, informação incompleta ou ambiguidade sobre como uma tela ou fluxo se
comporta, **pare e pergunte ao usuário antes de escrever qualquer coisa no manual.** Explique por
que a pergunta é necessária e como a resposta muda o texto. Nunca preencha uma lacuna com suposição
ou "achismo". Isso vale mesmo que pareça óbvio — o manual será usado por estudantes de Direito que
vão seguir os passos ao pé da letra; um passo errado gera confusão em sala de aula.

**O que deve existir ao final de todo o trabalho (não desta sessão, do projeto completo):**
- `manual-usuario/MANUAL_DO_USUARIO.md` — o manual completo.
- `manual-usuario/assets/` — as capturas de tela referenciadas pelo manual, conforme a
  especificação da Seção 9 deste roteiro.

O manual **não** precisa ser escrito de uma vez. Ele deve avançar capítulo por capítulo, com
validação do usuário a cada capítulo fechado (ver checklist na Seção 11).

---

## 1. Aviso obrigatório sobre documentação antiga — NÃO USAR COMO REFERÊNCIA

Existem, na pasta `docs-tuto/` (não versionada, separada desta pasta `manual-usuario/`), tentativas
anteriores de manual e de mapeamento do sistema:

- `docs-tuto/MANUAL_DO_USUARIO_v2.1.md` (e as versões v1/v2 anteriores a ela)
- `docs-tuto/guia-estrutura-apps-e-responsabilidades.md`
- `docs-tuto/arquitetura-referencia-projudi-django.md`
- `docs-tuto/mapa-mental/*.html` (`fluxo_movimentacoes_projudi.html`, `mapa_mental_projudi.html`,
  `movimentacoes_projudi.html`, `fluxograma_projudi_3.html`)

**Nenhum desses arquivos deve ser lido, citado ou usado como referência para este manual.**
Motivos, conforme o dono do projeto explicou:

- O conteúdo está **desatualizado em relação ao código atual** — foram escritos antes de o módulo
  de movimentações ser reconstruído e antes de existirem os apps `agendamentos` e `notificacoes`.
- Foram escritos **para outra versão da interface visual do sistema** — os prints que planejavam
  tirar (a v2.1 chegou a listar 33 imagens a capturar) não servem mais, porque as telas mudaram.
- **Não existia, até este roteiro, um padrão rigoroso de captura de imagem.** O padrão definido na
  Seção 9 deste documento é o primeiro a valer de forma obrigatória — não é uma continuação de
  nenhum padrão anterior.
- **Esses arquivos serão apagados** do repositório ao final da produção deste manual. O manual
  novo precisa se sustentar sozinho, sem depender deles.

**Única exceção:** este roteiro já verificou, contra o código atual, alguns fatos que continuam
verdadeiros (não porque estavam nos documentos antigos, mas porque foram reconferidos agora) — eles
estão inclusos diretamente na Seção 3 abaixo. O executor não precisa (e não deve) abrir os arquivos
antigos para obter isso; está tudo aqui.

Se, durante o trabalho, o executor sentir necessidade de abrir um desses arquivos antigos "só para
entender melhor o contexto", **pare e pergunte ao usuário antes** — pode ser um sinal de que falta
informação neste roteiro, e é melhor completá-lo do que reintroduzir conteúdo desatualizado.

---

## 2. Contexto do sistema

### 2.1 O que é o simu-projudi

O simu-projudi é um **simulador acadêmico** do sistema Projudi (o processo judicial eletrônico do
Tribunal de Justiça do Estado de Goiás — TJGO), usado por Núcleos de Prática Jurídica (NPJ) de
cursos de Direito para que estudantes pratiquem o peticionamento e a movimentação processual em um
ambiente seguro, com dados fictícios e sem qualquer valor jurídico real.

Stack técnica (relevante só para o executor entender onde procurar as coisas, não para o manual):
Django 6 + MySQL + Tailwind CSS, aplicação renderizada no servidor (sem API REST separada) — as
telas são views Django + templates HTML.

### 2.2 Apps do projeto e o que cada um governa

Levantamento feito diretamente na estrutura de pastas do repositório (não em documentação antiga).
Cada "app" é uma pasta na raiz do repositório com sua própria lógica. Ao investigar uma tela ou
ação para o manual, comece pelo app dono dela — e **confirme a responsabilidade de cada app lendo
o próprio código**, a tabela abaixo é só um ponto de partida de onde procurar:

| App | O que parece governar (a confirmar lendo o código) | Onde procurar |
|---|---|---|
| `acesso/` | Identidade e permissões: cadastro, login, aprovação de usuários, perfis (Admin, Coordenador, Professor, Aluno, Pendente) | `views.py`, `urls.py`, `permissions.py`, `templates/acesso/` |
| `usuarios/` | Existe como app separado de `acesso` — **o executor precisa ler `usuarios/models.py` e `usuarios/views.py` para entender a divisão exata de responsabilidade entre os dois apps antes de escrever qualquer seção sobre cadastro/perfil.** Não presumir que é redundante com `acesso`. | `views.py`, `models.py`, `forms.py`, `urls.py` |
| `ciclos/` | Gestão acadêmica: semestres letivos (ciclos de simulação) e grupos de trabalho dentro de um ciclo. Contém o cadastro de apoio `CargoSimulacao` (ver Seção 3.2). | `views.py`, `permissions.py`, `models.py`, `templates/ciclos/` |
| `processos/` | Núcleo judiciário: cadastro e visualização de processos, partes, polos | `views.py`, `permissions.py`, `templates/processos/` |
| `movimentacoes/` | Linha do tempo do processo: petições, despachos, juntada de documentos, catálogo de tipos de movimentação | `views.py`, `permissions.py`, `templates/movimentacoes/` |
| `avaliacoes/` | Avaliação (nota e feedback) de movimentações pelo professor | `views.py`, `permissions.py`, `templates/avaliacoes/` |
| `agendamentos/` | App sem documentação em qualquer manual anterior. Antes de escrever qualquer coisa sobre ele, leia `agendamentos/models.py`, `agendamentos/views.py` e os templates para confirmar o que está realmente funcional. | `views.py`, `models.py`, templates |
| `notificacoes/` | App sem documentação em qualquer manual anterior. Tem `services.py` e `context_processors.py`, o que sugere lógica de notificação ativa (não apenas decorativa) — confirme antes de descrever. | `views.py`, `services.py`, templates |
| `arquivos_privados/` | Armazenamento de documentos processuais (`django-private-storage`, conforme regras gerais do projeto) — confirme no código o que é exposto ao usuário final vs. o que é só infraestrutura. | `views.py`, `models.py` |
| `base/` | Componentes visuais compartilhados (botões, campos, modais, cards) e layout comum | não é fonte de fluxo de usuário, só de aparência |
| `core/` | Dashboards e páginas transversais (home, busca global) | `views.py`, templates |

### 2.3 Perfis de usuário e grupos internos de processo

Dois níveis de "quem pode fazer o quê" existem no sistema — **confirme ambos lendo
`acesso/permissions.py` e `movimentacoes/permissions.py` antes de escrever qualquer seção**:

- **Perfil global do usuário** (hierarquia): Admin > Coordenador > Professor > Aluno > Pendente.
  Um usuário "Pendente" é alguém que se cadastrou mas ainda não foi aprovado — não deve conseguir
  usar o sistema além de ver uma tela de espera.
- **Grupo dentro de um processo** (papel processual simulado, cadastro `CargoSimulacao` do app
  `ciclos`): ver códigos confirmados na Seção 3.2. Um aluno é alocado a um desses grupos dentro de
  um ciclo, e isso determina quais processos ele enxerga e quais movimentações pode praticar — a
  função `grupo_processo_do_usuario()` em `movimentacoes/permissions.py` é o ponto central disso.

---

## 3. O que já foi verificado no código atual (pode ser usado direto, sem reconferir a origem)

Esta seção existe para que o executor **não precise abrir os documentos antigos da Seção 1**. Tudo
abaixo foi checado contra o código do projeto nesta rodada de levantamento.

### 3.1 Termos institucionais (verdadeiros independente do código, são nomes do mundo real)

| Sigla | Significado |
|---|---|
| NPJ | Núcleo de Prática Jurídica |
| PROJUDI | Processo Judicial Digital — sistema eletrônico oficial do TJGO, do qual o simu-projudi é um simulador acadêmico |
| TJGO | Tribunal de Justiça do Estado de Goiás |
| CNJ | Conselho Nacional de Justiça |

Esses quatro termos não dependem do código — são nomenclatura institucional real e podem entrar
direto no glossário do manual.

### 3.2 Códigos de grupo processual (`CargoSimulacao`, app `ciclos`) — confirmados no código, com ressalva

`ciclos/models.py` define o modelo `CargoSimulacao` com um campo livre `cod` (não é uma lista fixa
de choices no Python — os valores reais vêm de dados cadastrados, provavelmente via migração ou
seed). Um comentário no próprio `models.py` documenta os códigos convencionados:

| Código | Nome |
|---|---|
| SC | Serventia/Cartório |
| APA | Advogados do Polo Ativo |
| APP | Advogados do Polo Passivo |
| MP | Ministério Público |
| JZ | Juiz |

**Confirmado em uso real:** esses cinco códigos (`SC`, `APA`, `APP`, `MP`, `JZ`) aparecem
ativamente em `movimentacoes/permissions.py` e na suíte de testes
`movimentacoes/tests/test_catalogo_tipos.py` — não são só um comentário morto.

**Ressalva que o executor precisa resolver antes de publicar o glossário:** como `cod` é um campo
livre e não um enum, o executor deve confirmar **onde esses cinco registros são de fato criados**
(procurar em migrações de dados do app `ciclos` ou em fixtures/seed) para garantir que continuam
sendo exatamente esses cinco nomes e códigos em produção, e que nenhum outro cargo foi adicionado
depois. Isso é rápido de checar e evita um glossário incompleto.

### 3.3 O que NÃO foi verificado e não deve ser assumido

Para deixar claro o limite do que pode ser usado sem reconferir: qualquer comportamento de tela,
qualquer afirmação sobre "o sistema gera X automaticamente", qualquer fluxo de aprovação de
cadastro, qualquer regra de prazo — **nada disso foi verificado nesta rodada** e precisa ser
levantado do zero pelo executor, lendo o código indicado na Seção 6. Em especial:
- O fluxo de cadastro → aprovação → login mudou recentemente (commit `88af589` — "fix:
  redirecionar cadastro público para login com mensagem de aprovação pendente"); o comportamento
  atual deve ser lido em `acesso/views.py`/`acesso/urls.py`, não assumido.
- O módulo de movimentações foi reconstruído (catálogo de tipos, regras de permissão, janela de
  correção) — nada sobre "como movimentar um processo" pode ser assumido sem ler
  `movimentacoes/views.py` e `movimentacoes/permissions.py` atuais.
- `agendamentos/` e `notificacoes/` nunca foram documentados — tratar como território
  desconhecido, 100% a levantar do zero.

---

## 4. Escopo e público-alvo

**Público-alvo do manual:** estudantes de graduação em Direito, professores e coordenadores de
Núcleo de Prática Jurídica que usam o simulador — pessoas do universo jurídico, não de TI.

**Perfis a cobrir no manual:** Admin, Coordenador, Professor, Aluno, e — dentro do fluxo de
processo — os grupos internos confirmados na Seção 3.2 (Polo Ativo, Polo Passivo, Ministério
Público, Juízo, Serventia/Cartório).

**Fora de escopo** (não incluir no manual do usuário final):
- Django admin técnico (`/admin/` do Django).
- Processo de deploy/infraestrutura.
- Arquitetura interna de código.

---

## 5. Linguagem e formato — diretriz de mercado adaptada ao público jurídico-acadêmico

Esta seção reproduz, adaptado ao simu-projudi, o material de referência de mercado que o dono do
projeto trouxe para orientar manuais de sistemas jurídicos. **Siga isto rigorosamente — não é uma
sugestão solta, é a régua de qualidade do documento.**

### 5.1 Linguagem direta
Evite termos técnicos de TI ("backend", "deploy", "model", "queryset") — o leitor não precisa saber
como o sistema é construído, só como usá-lo. Ao mesmo tempo, **não abuse do juridiquês**: mesmo o
público sendo de Direito, o manual ensina a operar um sistema, não redige uma peça processual —
seja claro e focado na ação. Termos jurídicos do domínio do Projudi (CNJ, comarca, vara, polo,
segredo de justiça) são esperados nesse público e devem ser explicados na primeira ocorrência.

### 5.2 Foco no fluxo de trabalho, não no módulo técnico
Nomeie capítulos e seções pela **tarefa que o usuário quer cumprir**, nunca pelo nome do app ou
módulo. Errado: "Módulo de Movimentações". Certo: "Como peticionar e anexar documentos" ou "Como
acompanhar o andamento do processo". O estudante pensa na tarefa, não na arquitetura do sistema.

### 5.3 Modelo fixo de passo a passo — Ação → Resultado
Todo tutorial segue esta estrutura: lista numerada de passos, cada um começando com um verbo de
ação ("Clique em...", "Preencha...", "Selecione..."), terminando em uma linha **Resultado:**
descrevendo o que o sistema faz em resposta. Exemplo (formato, não conteúdo — dados fictícios de
demonstração):

```
Como Cadastrar um Novo Processo
1. No menu lateral esquerdo, clique em Processos.
2. No canto superior direito, selecione o botão Novo Processo (+).
3. Preencha o número do processo (padrão CNJ) e os dados das partes.
4. Clique em Salvar.

Resultado: o processo é listado imediatamente na tela inicial e os prazos simulados começam a
ser monitorados.
```

### 5.4 Recursos visuais
O público lida com muito texto no dia a dia — o manual precisa se apoiar em capturas de tela para
reduzir a carga de leitura. **Neste projeto, por decisão do dono do sistema, as capturas não levam
seta nem destaque desenhado por cima** (ver justificativa e especificação técnica completa na
Seção 9) — a indicação de "onde clicar" fica só no texto do passo, de forma bem explícita (ex.: "no
canto superior direito, clique em **Novo Processo**").

### 5.5 Destaque de segurança e prazos
O público de Direito é obcecado por prazo e por segurança da informação. Sempre que uma tela
tratar de prazo (mesmo simulado) ou de dado sensível, isso precisa ficar **visível no corpo do
texto**, não em nota de rodapé — inclusive citando LGPD quando a tela expuser dado pessoal
(nome de parte, CPF/CNPJ fictício, etc.), mesmo sendo um ambiente acadêmico com dados fictícios.

### 5.6 Acessibilidade e navegação
O manual final em Markdown deve ter um índice no topo com links internos para cada seção (âncoras),
para que quem abrir o arquivo consiga pular direto para o capítulo que precisa — o documento vai
ser grande, cobrindo vários perfis.

### 5.7 Formatos variados (fora do escopo desta rodada, mas registrado para o futuro)
O material de mercado sugere complementar o manual em texto com pílulas de vídeo de ~1 minuto para
as funções mais complexas. **Isso não faz parte do escopo atual** (o formato definido é Markdown
com imagens — ver Seção 9) — não produzir vídeo nesta rodada. Só registrar aqui para não se perder,
caso o usuário peça isso em uma rodada futura.

---

## 6. Estrutura macro do manual

Usa a estrutura de seções lógicas recomendada pelo material de mercado (Introdução → Primeiros
Passos → Fluxos Principais → FAQ → Suporte), com os "Fluxos Principais" organizados de forma
híbrida: um bloco inicial único e sequencial comum a todos os perfis, seguido de um capítulo por
perfil (cada capítulo internamente sequencial). É a mesma lógica que o manual real do Projudi
(TJGO) usa — organiza seus manuais por perfil de usuário (Advogado, Analista Judiciário,
Cadastrador etc.), não como uma sequência única.

1. Capa e controle de versão.
2. Declaração de uso (documento acadêmico, dados fictícios, sem valor jurídico real).
3. Glossário de abreviações e siglas (começar pelo conteúdo já verificado na Seção 3.1 e 3.2 deste
   roteiro; expandir organicamente conforme novos termos aparecerem durante a escrita — sempre
   verificados no código ou, quando forem termos jurídicos genéricos como CNJ/comarca/vara,
   confirmados como termos do domínio real, não inventados).
4. Índice clicável (âncoras internas — ver Seção 5.6).
5. Introdução — o que é o simulador e por que ele ajuda na prática jurídica do curso.
6. **Primeiros Passos (comum a todos os perfis, nesta ordem exata):**
   1. Como se cadastrar no sistema.
   2. O que acontece logo após o cadastro (tela/estado de aprovação pendente).
   3. Como fazer login.
   4. Para onde cada perfil é redirecionado após o login.
7. **Fluxos Principais — um capítulo por perfil** (nesta ordem): Admin → Coordenador → Professor →
   Aluno. Dentro do capítulo de fluxo de processo, cobrir também os grupos internos (Polo Ativo,
   Polo Passivo, MP, Juízo, Serventia/Cartório).
8. Resolução de Problemas (FAQ) — perguntas frequentes, estilo pergunta/resposta direta.
9. Suporte e Contato — canais de atendimento (confirmar com o usuário quais existem antes de
   escrever esta seção; não inventar canal de suporte).
10. "Funcionalidades em Fase de Homologação Acadêmica" — funcionalidades com interface pronta mas
    sem lógica ativa (ver regra na Seção 7).
11. Apêndice — lista consolidada de todas as capturas de tela do manual (ver Seção 9).

---

## 7. Regras de redação adicionais

- Cada seção declara logo no início: (a) quem pode executar aquela ação — perfil e/ou grupo — e
  (b) o que precisa existir antes (pré-requisito). Exemplo: "Esta ação está disponível para
  Professor e Coordenador. Pré-requisito: o ciclo precisa estar ativo."
- **Funcionalidade com interface pronta mas sem lógica ativa** (aparece na tela mas não faz nada ao
  clicar, ou mostra dado estático) entra na seção separada "Funcionalidades em Fase de Homologação
  Acadêmica" (Seção 6, item 10) — nunca misturada aos fluxos que realmente funcionam. Antes de
  classificar algo nessa seção, confirme no código que de fato não há lógica por trás (não é só
  falta de dados de teste).

---

## 8. Sequência de execução, passo a passo

Siga esta ordem. Cada item indica exatamente onde olhar no repositório.

1. **Mapear permissões.** Leia `acesso/permissions.py`, `ciclos/permissions.py`,
   `processos/permissions.py`, `movimentacoes/permissions.py`, `avaliacoes/permissions.py`, e o
   que existir em `agendamentos/` e `notificacoes/` (verifique se têm `permissions.py` próprio; se
   não tiverem, a lógica de acesso pode estar direto na view). Leia também `usuarios/models.py` e
   `usuarios/views.py` para esclarecer a divisão de responsabilidade com o app `acesso` (ver
   Seção 2.2). Produza uma tabela interna de trabalho: ação → quem pode fazer → pré-requisito.

2. **Mapear a jornada comum.** Leia `acesso/views.py` e `acesso/urls.py` para reconstruir, passo a
   passo, o que acontece desde o formulário público de cadastro até o usuário cair na tela inicial
   do seu perfil. Preste atenção especial ao efeito do commit `88af589` — confirme no código atual
   (não em memória do commit) qual é a mensagem exibida e para onde o usuário é levado após se
   cadastrar, antes de ser aprovado.

3. **Mapear cada capítulo de perfil, em ordem de uso real** (não em ordem alfabética nem por
   ordem de arquivo):
   - **Admin:** gestão de ciclos → gestão de usuários (aprovação de cadastro pendente) → gestão de
     grupos do ciclo. Arquivos: `ciclos/views.py`, `acesso/views.py`.
   - **Coordenador:** visão geral de ciclos, o que muda em relação ao Admin (se houver
     restrição). Confirme a diferença real de permissão em `ciclos/permissions.py`, não suponha
     que é igual ao Admin.
   - **Professor:** acompanhar processos do seu grupo/ciclo → avaliar movimentações de alunos.
     Arquivos: `processos/views.py`, `avaliacoes/views.py`.
   - **Aluno:** ver processos do seu grupo → cadastrar/movimentar processo (conforme seu grupo
     processual) → ver avaliação recebida. Arquivos: `processos/views.py`,
     `movimentacoes/views.py`.
   - **Grupos internos de processo** (Polo Ativo, Polo Passivo, MP, Juízo, Serventia/Cartório):
     documentar as diferenças de acesso entre eles dentro do capítulo do Aluno — em especial, o
     grupo Serventia/Cartório parece enxergar todos os processos do ciclo, enquanto os demais só
     veriam os processos atribuídos ao próprio grupo — **confirme isso em
     `movimentacoes/permissions.py::grupo_processo_do_usuario` antes de afirmar**, esta frase é uma
     hipótese a checar, não um fato já verificado.

4. **Cobrir `agendamentos/` e `notificacoes/` como capítulos próprios ou subseções**, decidindo o
   encaixe conforme o que a leitura do código revelar (podem ser transversais a todos os perfis, ou
   específicos de um). Como são apps sem documentação anterior, não presuma nada sobre eles —
   leia `models.py`, `views.py` e os templates por completo antes de escrever uma linha.

5. **Documentar o catálogo de tipos de movimentação por categoria**, não um a um (o catálogo é
   grande — listar e explicar cada tipo individualmente tornaria o manual impraticável). Agrupe por
   finalidade (ex.: petições, despachos, juntada de documento, decisões) da forma como o código em
   `movimentacoes/models.py` ou a migração/fixture de dados já os organiza. Se o usuário quiser
   depois um detalhamento maior, isso é uma decisão dele, não do executor.

6. **Montar a "Lista de Capturas"** de cada capítulo, na tabela definida na Seção 9, antes de
   escrever o texto final do capítulo — assim a lista de capturas nasce alinhada ao texto.

7. **Escrever o texto tela por tela**, na ordem do levantamento, aplicando as regras das Seções 5
   e 7.

8. **Revisão cruzada:** releia cada seção escrita comparando com o código-fonte mais uma vez antes
   de considerar o capítulo fechado. É comum, ao escrever, introduzir uma afirmação que não foi de
   fato conferida — esta etapa existe para pegar isso.

9. **Checkpoint com o usuário ao final de cada capítulo** (não esperar o documento inteiro ficar
   pronto para mostrar). Ver critério de fechamento de capítulo na Seção 11.

---

## 9. Especificação técnica dos prints — padrão obrigatório, sem exceção

**Não existia, antes deste roteiro, nenhum padrão rigoroso de captura de imagem no projeto** — a
tentativa anterior listava imagens a tirar mas não definia formato/tamanho de forma vinculante, e
foi feita para uma versão antiga da interface. A partir de agora, **toda captura de tela deste
manual segue exatamente a tabela abaixo, sem exceção**:

| Especificação | Valor |
|---|---|
| **Formato de arquivo** | PNG (preferencial, sem perda de qualidade). JPG só se o PNG ficar pesado demais para o documento. |
| **Largura máxima** | 1200 px — redimensionar após a captura se o monitor usado for maior. |
| **Altura** | Livre, conforme o conteúdo real da tela (não recortar arbitrariamente). |
| **Enquadramento padrão** | Tela inteira do navegador, sem barra de endereço nem abas do sistema operacional. |
| **Enquadramento de recorte** | Só quando a "Lista de Capturas" do capítulo pedir explicitamente um recorte de um elemento específico (ex.: um modal, um card) — nesse caso, capturar só aquele bloco. |
| **Zoom do navegador** | 100% (sem zoom in/out), para manter a proporção real de fonte e ícone do sistema. |
| **Dados de exemplo nas telas** | Sempre fictícios e neutros — nomes, números de processo e valores inventados, nunca dado real de aluno ou professor. |
| **Anotação sobre a imagem** | Nenhuma. Sem seta, sem retângulo, sem destaque desenhado — a indicação de onde clicar fica só no texto do passo (Seção 5.4). |
| **Nomenclatura do arquivo** | `img_XX_descricao-curta.png`, numeração sequencial pela ordem de aparição no manual (ex.: `img_07_cadastro_processo_passo1.png`). |
| **Pasta de destino** | `manual-usuario/assets/` |
| **Sintaxe de inserção no Markdown** | `![Descrição da imagem](assets/img_XX_descricao.png)` — o texto alternativo deve descrever o conteúdo da tela para acessibilidade. |

Cada capítulo do manual deve conter, antes das imagens propriamente ditas, uma tabela "Lista de
Capturas" neste formato:

| ID | Nome do arquivo | Rota/tela | Dado de exemplo a preencher | Recorte (cheia ou elemento) |
|---|---|---|---|---|
| IMG-01 | `img_01_login.png` | `/login/` | — | Tela cheia |

Enquanto as capturas reais não existirem, o corpo do manual usa um marcador de texto no lugar da
imagem, no formato `[IMAGEM XX: descrição detalhada do que deve aparecer na captura]`, substituído
pela tag Markdown de imagem assim que o arquivo existir em `assets/`.

---

## 10. Quando parar e perguntar (não presumir)

Interrompa a escrita e pergunte ao usuário sempre que:

- Uma funcionalidade tiver interface visual mas o comportamento no código for ambíguo, incompleto,
  ou você não conseguir determinar com certeza se está ativa.
- Faltar decidir em que capítulo uma funcionalidade transversal (como `agendamentos` ou
  `notificacoes`) deve entrar.
- Antes de fechar a lista de capturas de tela de um capítulo — confirme com o usuário se a lista
  está completa e no nível de detalhe esperado antes de considerar o capítulo pronto para captura.
- Sentir vontade de abrir um dos documentos antigos listados na Seção 1 "para entender melhor" —
  isso é sinal de lacuna neste roteiro, não motivo para reabrir material desatualizado.
- Qualquer situação não prevista explicitamente por este roteiro.

Ao perguntar, explique **por que** a pergunta é necessária e **como cada resposta possível muda o
texto do manual** — não faça perguntas genéricas sem contexto.

---

## 11. Convenções de arquivo e pasta

- Pasta do manual: `manual-usuario/`, na raiz do repositório (versionada — ver aviso no topo do
  documento).
- Arquivo principal do manual: `manual-usuario/MANUAL_DO_USUARIO.md`.
- Imagens: `manual-usuario/assets/`, seguindo a nomenclatura da Seção 9.
- Este roteiro: `manual-usuario/ROTEIRO.md` (não editar a estrutura dele durante a
  escrita do manual — se uma regra precisar mudar, isso é uma decisão do usuário, não do
  executor).

## 12. Checklist de conclusão de cada capítulo

Antes de considerar um capítulo pronto e passar para o próximo, confirme:

- [ ] Cada passo foi conferido no código-fonte atual (nunca copiado de material antigo sem
      reconferir — e o material antigo da Seção 1 nem deveria ter sido aberto).
- [ ] O modelo Ação → Resultado foi aplicado em todos os tutoriais do capítulo.
- [ ] A "Lista de Capturas" do capítulo está completa e segue a especificação da Seção 9 à risca
      (formato, tamanho, sem anotação).
- [ ] Perfil/grupo autorizado e pré-requisitos estão declarados no início de cada seção.
- [ ] Nenhuma afirmação foi feita por suposição — toda dúvida foi levada ao usuário (Seção 10).
- [ ] O usuário validou o capítulo antes de o executor seguir para o próximo.
