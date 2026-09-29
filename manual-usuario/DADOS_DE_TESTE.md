# Dados de Teste — Manual do Usuário simu-projudi

> Documento de controle interno, **não faz parte do manual entregável**. Lista todos os usuários,
> senhas, grupos e processos fictícios criados para produzir as capturas de tela do manual.
> Mantido em `manual-usuario/`, na raiz do repositório (pasta versionada na branch
> `docs/manuais` — ver aviso de segurança sobre este arquivo antes de fazer commit).

Última atualização: 2026-09-17

---

## Convenções adotadas (aprovadas pelo usuário em 2026-09-17)

- **Nomes fictícios**: nomes completos plausíveis (nunca "usuario01", "aluno-teste" etc.).
- **E-mail**: `nome.sobrenome@exemplo.com`
- **Senha padrão de todos os usuários de teste**: `Simu@Teste2026`
  (atende aos requisitos exibidos na própria tela de cadastro: mínimo 8 caracteres, não
  inteiramente numérica, não comum, não similar aos dados pessoais)

## Padrão técnico de captura de tela (resolvido em 2026-09-17)

- Captura feita com acesso real ao Chrome do usuário (extensão Claude in Chrome), navegando e
  preenchendo os formulários de verdade — nunca simulação/mockup.
- Screenshot é tirado na resolução nativa da janela do navegador (sem barra de endereço nem abas
  do SO — a ferramenta já captura só o conteúdo da página).
- Em seguida, a imagem é redimensionada para **largura máxima de 1200px** (mantendo proporção) e
  salva como PNG — conforme permitido pela própria Seção 9 do ROTEIRO.md ("redimensionar após a
  captura se o monitor usado for maior").
- O arquivo final é copiado direto para `manual-usuario/assets/` no computador do usuário.

---

## Usuário Admin (já existia antes desta sessão, não foi criado por mim)

| Campo | Valor |
|---|---|
| Usuário (login) | `admin` |
| E-mail | admin@gmail.com (visto no painel "Todos os Usuários") |
| Senha | *(omitida deste documento — não versionar credencial, mesmo de teste)* |
| Perfil | Admin |
| Nome exibido no sistema | Halbert |

---

## Usuários criados nesta sessão

### 1. Mariana Albuquerque Teixeira

| Campo | Valor |
|---|---|
| Nome completo | Mariana Albuquerque Teixeira |
| E-mail (= username) | mariana.teixeira@exemplo.com |
| Senha | Simu@Teste2026 |
| Perfil global | **Aluno** — aprovado e ativo em 17/09/2026, pelo Coordenador (Ricardo), via painel administrativo |
| Status atual | Ativo. Fez login e caiu em "Boas-vindas" (`/ciclos/boas-vindas/`) com status "Aguardando Vínculo" — ainda não foi incluída em nenhum grupo de trabalho/ciclo |
| Criada para | Capítulo "Primeiros Passos" → Cadastro / Estado Pendente / tentativa de login antes da aprovação (IMG-04) |

### 2. Ricardo Bandeira Cavalcanti

| Campo | Valor |
|---|---|
| Nome completo | Ricardo Bandeira Cavalcanti |
| E-mail (= username) | ricardo.cavalcanti@exemplo.com |
| Senha | Simu@Teste2026 |
| Perfil global | **Coordenador** — aprovado e ativo em 17/09/2026, pelo Admin, via painel administrativo (`/acesso/painel-administrativo/` → Analisar Cadastros → Aprovar/Editar → Tipo de Perfil = Coordenador + Ativo) |
| Status atual | Ativo, pode logar normalmente |
| Criada para | Capítulo "Primeiros Passos" → tela de cadastro preenchida (IMG-02) e tela de sucesso do cadastro (IMG-03). Também vai ser o Coordenador usado para aprovar os próximos usuários de teste. |

---

## Fatos confirmados nesta sessão (via código + comportamento real da tela, não suposição)

1. **Fluxo de cadastro** (`acesso/views.py::cadastrar`): formulário público pede só Nome Completo,
   Email, Senha e Confirmação de senha. Ao salvar, o sistema força
   `tipo_perfil_global=Pendente` e `is_active=False`, e usa o e-mail como `username`.
   Após o envio, o usuário é redirecionado para a tela de login com a mensagem de sucesso:
   > "Cadastro realizado com sucesso! Aguarde a aprovação de um responsável para acessar o sistema."

2. **Quem aprova o cadastro**: o texto da própria tela de login ("Primeiro Acesso — Liberação pelo
   Coordenador") diz que é o **Coordenador** quem confirma a matrícula e atribui o cargo de
   simulação — não um "responsável" genérico como a mensagem de sucesso sugere. O card "Como
   funciona" na tela de cadastro cita "administrador, coordenador ou professor" como quem pode
   ativar. **Confirmado na prática**: o Admin também consegue aprovar/editar qualquer cadastro
   pendente pelo Painel de Controle → "Analisar Cadastros" (a permissão real, por trás,
   é `pode_gerenciar_usuarios` combinada com `tipos_que_pode_atribuir`, de
   `acesso/permissions.py` — ainda preciso ler esse arquivo para confirmar se Professor também
   aparece na prática, ou só na mensagem).

3. **Tela "Gestão de Usuários"** (modal aberto pelo botão "Analisar Cadastros" ou "Gerir
   Usuários" no Painel de Controle): tem abas "Pendentes" (com contador) e "Todos os Usuários"
   (com busca por nome/e-mail). Ao aprovar/editar um usuário pendente, abre um formulário com
   "Tipo de Perfil" (select: Admin, Coordenador, Professor, Aluno) e um checkbox "Ativo (liberar
   acesso ao sistema)" — os dois precisam ser preenchidos/marcados manualmente; não há um botão
   único de "aprovar com 1 clique" que já libera automaticamente.

4. **Tentativa de login com cadastro Pendente**: testado de fato (login com
   mariana.teixeira@exemplo.com / Simu@Teste2026 antes de qualquer aprovação). O sistema **não**
   mostra uma mensagem específica de "conta pendente" — mostra o erro genérico padrão do Django:
   > "Por favor, entre com um usuário e senha corretos. Note que ambos os campos diferenciam
   > maiúsculas e minúsculas."
   Isso é porque `is_active=False` impede a autenticação antes mesmo da checagem de perfil.
   **Importante para o manual**: avisar o aluno que, entre o cadastro e a aprovação, tentar logar
   vai parecer "senha errada", não "aguardando aprovação" — vale destacar isso no manual para
   evitar confusão.

5. **E-mail de suporte real** (exibido na tela de login, card "Suporte"): `simulador@tjgo.jus.br`.

6. **Requisitos de senha** exibidos na própria tela de cadastro (batem com
   `AUTH_PASSWORD_VALIDATORS` em settings): mínimo 8 caracteres; não pode ser inteiramente numérica;
   não pode ser senha comum; não pode ser similar aos dados pessoais do usuário.

7. **Cards "Manuais de Utilização" na tela de login** (todos "Em breve", ou seja, funcionalidade de
   interface pronta mas sem conteúdo ativo — candidato à seção "Funcionalidades em Fase de
   Homologação Acadêmica"): confirma visualmente os mesmos 5 grupos processuais da Seção 3.2 do
   ROTEIRO.md: Serventia/Cartório (SC), Advogados Polo Ativo (APA), Advogados Polo Passivo (APP),
   Ministério Público (MP), Juiz (JZ) — mais um card "Geral" (Guia geral do simulador).

8. **Outros avisos exibidos na tela de login** (painel "Informações Importantes", ainda não
   verificados a fundo no código, só capturados como texto de tela — a confirmar antes de entrar no
   manual): limite de 7 MB por arquivo enviado; sessão encerra após 15 minutos sem atividade;
   processos em segredo de justiça (aviso especial). Há um link "+ informações importantes" que
   sugere mais itens além dos visíveis.

9. **Painel de Controle do Admin/Coordenador/Professor** (`acesso/views_admin_usuarios.py::painel_administrativo`,
   docstring do próprio código avisa): as listagens de usuários/ciclos/processos vêm **sem
   paginação no servidor** de propósito (paginação e busca acontecem no navegador) — isso é uma
   decisão consciente registrada no código, não um bug, mas o próprio código avisa que vai
   precisar de paginação no servidor quando o volume de dados crescer. **Não é** algo a documentar
   como "problema" no manual, mas explica por que a tela pode ficar lenta com muitos ciclos no
   futuro — não é relevante para o usuário final, só anotado aqui para contexto.
   Também reparei que o "Resumo do Semestre (Atual)" mostrava números (Processos Ativos 45,
   Avaliações Pendentes 12, Grupos de Trabalho 8, Alunos Vinculados 20/0 — mudou entre um clique e
   outro) **mesmo com "Nenhum ciclo de simulação cadastrado"** — preciso investigar se são dados
   de seed pré-existentes no banco (de antes desta sessão) ou se há inconsistência a esclarecer
   antes de descrever esse painel no manual. Ainda não verificado a fundo — não usar esses números
   no manual até confirmar a origem.

---

## Capturas de tela já produzidas

| ID | Arquivo | Conteúdo | Rota | Capítulo do manual |
|---|---|---|---|---|
| IMG-01 | `img_01_cadastro_vazio.png` | Formulário de cadastro em branco | `/acesso/cadastro/` | Primeiros Passos → Cadastro |
| IMG-02 | `img_02_cadastro_preenchido.png` | Formulário preenchido (dados do Ricardo) | `/acesso/cadastro/` | Primeiros Passos → Cadastro |
| IMG-03 | `img_03_cadastro_sucesso.png` | Tela de login com a mensagem de sucesso do cadastro | `/acesso/` | Primeiros Passos → Cadastro |
| IMG-04 | `img_04_login_pendente_erro.png` | Tentativa de login com cadastro ainda Pendente (erro genérico) | `/acesso/` | Primeiros Passos → Cadastro |
| IMG-05 | `img_05_admin_aprovacao_coordenador.png` | Modal "Gestão de Usuários" → aba "Todos os Usuários", já com Ricardo como Coordenador Ativo | `/acesso/painel-administrativo/` | (reservado p/ capítulo do Admin — gestão de usuários) |

---

## Pendências / decisões em aberto (aguardando o usuário)

- Ainda preciso criar usuários fictícios para: Professor, e pelo menos um Aluno por grupo
  processual (SC, APA, APP, MP, JZ) — nomes a definir e aprovar.
- Investigar a origem dos números do "Resumo do Semestre" no painel administrativo antes de usá-los
  em qualquer captura/texto do manual (ver item 9 dos fatos confirmados).
- Preciso de um Professor (ou do próprio Coordenador) pra vincular a Mariana a um ciclo/grupo e ver
  a tela do lado de quem já tem processo pra acompanhar — hoje ela só mostra a tela "Aguardando
  Vínculo".

---

## Mais fatos confirmados (rodada 2 — aprovação da Mariana e login dela)

10. **Dropdown "Tipo de Perfil" muda conforme quem está aprovando**: logado como Admin, o select
    tinha as opções Admin/Coordenador/Professor/Aluno. Logado como **Coordenador (Ricardo)**, o
    mesmo formulário só oferece Coordenador/Professor/Aluno — **sem a opção Admin**. Confirma que
    `tipos_que_pode_atribuir()` realmente limita por perfil, não é só um texto de tela — precisa
    entrar em `acesso/permissions.py` para confirmar a regra exata antes de escrever isso no
    manual como afirmação geral.

11. **Painel de Controle do Coordenador é visualmente idêntico ao do Admin** (mesma tela, mesmos
    números do "Resumo do Semestre", mesmas Ações Rápidas). Ainda não testei se as ações (ex.:
    "Distribuir Novo Processo", "Agendar Audiência") têm comportamento diferente na prática —
    só a tela de entrada é igual.

12. **Login de Aluno aprovado mas sem vínculo de grupo/ciclo**: NÃO cai em `processos:pagina_aluno`
    (como o comentário do código em `acesso/views.py` sugeria) — cai em `/ciclos/boas-vindas/`,
    com um cartão "Situação do Cadastro: Aguardando Vínculo" explicando: *"É o professor ou o
    coordenador do ciclo quem inclui você em um grupo e define o cargo que vai exercer na
    simulação — Serventia, Advogado, Ministério Público ou Juiz."* Ou seja, o redirect real
    depende de mais uma condição (ter ou não vínculo) que o código de `acesso/views.py` sozinho não
    deixa claro — a lógica de decidir entre "página do aluno" e "boas-vindas" deve estar dentro de
    `processos:pagina_aluno` (view), não em `acesso/views.py`. **Preciso ler essa view antes de
    escrever a seção "Para onde cada perfil é redirecionado" no manual.**

13. **Termo usado na própria tela para os grupos processuais**: "Serventia, Advogado, Ministério
    Público ou Juiz" — nota que aqui aparece só "Advogado" (sem separar Polo Ativo/Passivo), ao
    contrário da distinção SC/APA/APP/MP/JZ do `ciclos/models.py`. Pode ser só um texto
    simplificado de boas-vindas — **não tratar como contradição ainda, mas confirmar quando eu
    mapear a tela real de vínculo de grupo.**


---

## Usuário criado (rodada 3) — Professor

### 3. Camila Ferreira Duarte

| Campo | Valor |
|---|---|
| Nome completo | Camila Ferreira Duarte |
| E-mail (= username) | camila.duarte@exemplo.com |
| Senha | Simu@Teste2026 |
| Perfil global | **Professor** — aprovado e ativo em 17/09/2026, pelo Coordenador (Ricardo) |
| Status atual | Ativo. Ainda não logou nem foi vinculada a nenhum ciclo/grupo como coordenadora específica. |
| Criada para | Testar o capítulo do Professor (pendente) e possivelmente ser reatribuída como "coordenador" do ciclo NPJ Cível 2026/2 |

---

## BLOQUEIO ENCONTRADO E RESOLVIDO: tabela "Status dos Ciclos" vazia

A tabela `StatusCiclo` (admin: Ciclos → Status dos Ciclos) estava **com 0 registros** neste
ambiente. Isso impedia até o botão "+ Novo Ciclo" de aparecer no Painel de Controle — o template
`painel_administrativo.html` só renderiza esse botão se `status_ciclo_opcoes` (contexto vindo de
`StatusCiclo.objects.all()`) não estiver vazio. Ou seja: **sem esses registros, absolutamente
ninguém conseguiria criar um ciclo pela interface**, independente de perfil/permissão.

Em contraste, `CargoSimulacao` (SC/APA/APP/MP/JZ) já estava com os 5 registros certos — resolve de
vez a ressalva da Seção 3.2 do ROTEIRO.md, esses 5 códigos são exatamente os usados em produção.

**Ação tomada, com aprovação prévia do usuário**: cadastrei manualmente, pelo Django admin
(`/admin/ciclos/statusciclo/add/`, logado como `admin`), os 3 registros que o código já espera
(comparações `__iexact` em `ciclos/views.py` e `ciclos/permissions.py`):
- `em andamento`
- `finalizado`
- `arquivado`

Isso não alterou nenhum arquivo de código — só inseriu dados de referência faltando. Depois disso
o botão "+ Novo Ciclo" passou a aparecer normalmente.

**Nota sobre o Django admin**: só o usuário `admin` (superusuário) tem acesso a `/admin/`. Ricardo
(Coordenador) tentou acessar e recebeu "Você não tem permissão para ver ou editar nada." — confirma
que `is_staff`/`is_superuser` é exclusivo do Admin, não dos demais perfis globais.

---

## Ciclo, Grupo e vínculo criados (rodada 3)

| Campo | Valor |
|---|---|
| Nome do Ciclo | NPJ Cível 2026/2 |
| Semestre / Ano | 2º / 2026 |
| Status | Em andamento |
| Criado por | Ricardo Bandeira Cavalcanti (Coordenador) — quem cria um ciclo é automaticamente registrado como "Responsável"/coordenador dele (não há campo pra escolher outro coordenador na criação — só depois, editando) |
| Grupo de Trabalho | Albuquerque & Associados |
| Papel Processual do grupo | Advogados Polo Ativo (APA) |
| Membro do grupo | Mariana Albuquerque Teixeira (Aluno) |

**Fato confirmado**: ao criar um ciclo, **não existe campo pra escolher o Coordenador** — o
formulário só mostra nome, semestre e ano, com o aviso "Você será registrado automaticamente como
Coordenador deste ciclo." A opção de reatribuir esse campo a outra pessoa (ex.: um Professor) só
aparece na tela de **editar** um ciclo já existente (`ciclos/forms.py::CicloSimulacaoForm`, campo
extra "coordenador", disponível só quando `ator` é Admin ou Coordenador). **Ainda não fiz essa
reatribuição para a Camila** — pendente.

**Fato confirmado sobre o redirecionamento do Aluno**: depois que Mariana foi colocada no grupo
"Albuquerque & Associados", o login dela deixou de cair em `/ciclos/boas-vindas/` e passou a cair
em `/processos/area-servidor/` ("Área do Aluno"), mostrando o grupo dela ("Albuquerque & Associados
— Advogados Polo Ativo") e a lista de processos vinculados (vazia, porque nenhum processo foi
distribuído ainda para esse ciclo). Isso confirma que `processos:pagina_aluno` = `/processos/area-servidor/`,
e que essa view decide internamente entre mostrar a área normal ou redirecionar para
`/ciclos/boas-vindas/`, dependendo de o aluno ter ou não vínculo de grupo no ciclo ativo.

**Achado sobre o "Resumo do Semestre" (reforça a suspeita já registrada antes)**: mesmo depois de eu
criar o primeiro ciclo real do banco (0 grupos e processos reais no início), o card "Resumo do
Semestre" no Painel de Controle continuou mostrando "Grupos de Trabalho: 8" e "Alunos Vinculados:
20" — números que não batem com o estado real (na hora, era 0 grupos e 1 aluno). **Confirma que
esse card usa dado fixo/de outra fonte, não a contagem real dos ciclos visíveis** — não usar esses
números no manual. Isso merece ser investigado/reportado como algo a verificar com mais calma
(pode ser propositalmente fixo para demonstração, ou um bug) — não vou mexer nisso sem perguntar.

---

## Capturas de tela adicionais desta rodada

| ID | Arquivo | Conteúdo |
|---|---|---|
| IMG-07 | `img_07_ciclo_criado.png` | Painel do Coordenador com o ciclo "NPJ Cível 2026/2" já criado |
| IMG-08 | `img_08_grupo_com_mariana.png` | Tela "Gerenciar Grupos" com a Mariana já adicionada ao grupo Albuquerque & Associados |
| IMG-09 | `img_09_aluno_area_com_grupo.png` | "Área do Aluno" da Mariana, já mostrando o grupo e nenhum processo vinculado ainda |

---

## Mais fatos confirmados (rodada 4 — capítulo do Aluno, sem processo ainda)

14. **Menu do Aluno tem 4 itens**: Página Inicial, Processos, Audiências, Minhas Notas.
    - **Processos → Cadastrar Processos** (`/processos/cadastrar/`): link real, abre um wizard de
      3 passos "Cadastro de Processo Comum" (Dados do Processo / Documentos / Resumo), já mostrando
      o ciclo ativo do aluno no topo. Não preenchi/enviei o formulário ainda (fica pra quando formos
      distribuir de fato um processo de teste).
    - **Processos → Consultar Todos**: `href="#"` — **não funcional** (não navega pra lugar
      nenhum). Verificar se é feature pendente ou bug de template antes de citar no manual.
    - **Audiências** (item do menu superior): também `href="#"` — **não funcional**, mesma ressalva
      acima.
    - **Minhas Notas** (`/avaliacoes/minhas-notas/`): link real e funcional. Mostra painel "Meu
      Desempenho" (Média Geral, Avaliadas, Melhor Nota) e "Histórico de Avaliações". Com a Mariana
      sem nenhuma movimentação avaliada, todos os indicadores aparecem vazios ("—"/"0") e o
      histórico mostra "Nenhuma avaliação recebida ainda.".

15. **Notificações funcionam de verdade**: o sino no cabeçalho tem contador (badge) e, ao abrir,
    mostra o histórico de eventos relevantes pro usuário — testado com a Mariana, aparece
    "Você foi adicionado ao ciclo 'NPJ Cível 2026/2'." com o tempo relativo ("18 minutos atrás") e
    um link "Ver todas".

---

## Capturas de tela adicionais (rodada 4)

| ID | Arquivo | Conteúdo |
|---|---|---|
| IMG-13 | `img_13_aluno_minhas_notas_vazio.png` | Tela "Minhas Notas" da Mariana, sem nenhuma avaliação recebida ainda |
| IMG-14 | `img_14_aluno_notificacao_vinculo.png` | Painel de notificações da Mariana, mostrando o aviso de inclusão no ciclo |

---

## BLOQUEIO ENCONTRADO E RESOLVIDO (rodada 5): catálogos de processo vazios

Ao testar o formulário "Cadastrar Processos" (Aluno, Professor, Coordenador ou Admin — qualquer
perfil), os selects **Comarca**, **Vara/Serventia**, **Classe Processual** e o campo **Tipo do
Processo** apareciam completamente vazios (só a opção "Selecione..."). Confirmado no Django admin:
as tabelas `Comarca`, `VaraServentia`, `ClasseProcessual` e `TipoProcesso` estavam com **0
registros** — exatamente o mesmo padrão do bloqueio do `StatusCiclo` (Seção anterior). São tabelas
de catálogo simples (só `nome`, e `VaraServentia` também referencia uma `Comarca`), sem nenhuma
comparação de string fixa no código (`grep` em `processos/views.py` e `processos/forms.py` não
achou nenhum `iexact` dependente desses catálogos).

**Ação tomada, com aprovação prévia do usuário** (lista de nomes aprovada em chat, com a troca
pedida de "Goiânia" para "Formosa"): cadastrei manualmente, pelo Django admin, logado como `admin`:

| Catálogo | Registros cadastrados |
|---|---|
| Comarca | Formosa |
| Vara/Serventia | 1ª Vara Cível de Formosa; 2ª Vara Cível de Formosa (ambas em Formosa) |
| Classe Processual | Procedimento Comum Cível; Execução de Título Extrajudicial; Embargos de Terceiro |
| Tipo de Processo | Processo Comum |

Nenhum arquivo de código foi alterado — só dados de referência inseridos, igual ao caso do
`StatusCiclo`.

**Outro achado, não corrigido (é comportamento de tela, não dado faltando)**: o campo "*Assunto(s)"
do formulário de cadastro de processo é **puramente visual** — não existe nenhum model `Assunto`
no código (`grep -ri assunto` em todo o projeto só retorna o texto estático do template, sem
JS/model por trás). Mesmo sem preencher esse campo, o formulário avança normalmente e o processo é
cadastrado com sucesso — ou seja, apesar do asterisco (`*`) indicar campo obrigatório, ele não é
validado nem no front nem no back. **Não documentar "Assunto(s)" como funcional no manual.**

---

## Processo de teste cadastrado (rodada 5)

| Campo | Valor |
|---|---|
| Número (gerado automaticamente, padrão CNJ) | `0000001-74.2026.8.26.0001` |
| Tipo | Processo Comum |
| Comarca / Vara | Formosa — 1ª Vara Cível de Formosa |
| Classe Processual | Procedimento Comum Cível |
| Valor da causa | R$ 15.000,00 |
| Segredo de Justiça | Não |
| Polo Ativo | Antônio Ribeiro Pacheco — CPF 123.456.789-00 (Física) |
| Polo Passivo | Comércio Formosa de Materiais de Construção Ltda — CNPJ 12.345.678/0001-00 (Jurídica) |
| Ciclo | NPJ Cível 2026/2 |
| Grupo vinculado | Albuquerque & Associados (Advogados Polo Ativo) |
| Cadastrado por | Mariana Albuquerque Teixeira (Aluno) |
| Status | Protocolado |

**Fatos confirmados ao cadastrar**: o número do processo é gerado automaticamente pelo sistema no
formato CNJ (`NNNNNNN-DD.AAAA.J.TR.OOOO`) — não é digitado pelo usuário. O Passo 2 (Documentos) é
opcional: dá pra avançar sem anexar nada. O Passo 3 (Resumo) mostra um resumo de conferência antes
do cadastro definitivo.

**Movimentação de teste registrada**: logada como Mariana, usei "Opções Processo → Movimentar" no
processo recém-criado. O dropdown "Tipo de Movimentação" só ofereceu **uma opção para o perfil
Aluno/Advogado do grupo**: "Juntada de Documentos" — confirma que os tipos de movimentação
disponíveis são filtrados por papel processual (Advogado só pode juntar documentos; despacho,
sentença etc. devem ficar reservados a Juiz/Serventia — **ainda não testado, a confirmar quando
logar como esses perfis**). Registrei a movimentação "Juntada da procuração e documentos pessoais
do autor Antônio Ribeiro Pacheco." sem anexar arquivo (também opcional aqui). A tela de detalhe do
processo (aba "Eventos do Processo") passou a mostrar 2 eventos: "1 — Protocolo da Petição Inicial"
(automático, gerado no cadastro) e "2 — Juntada de Documentos" (a que acabei de registrar), cada um
com usuário e data/hora exatos.

**Menu "Opções Processo" (visto como Aluno/Advogado do Polo Ativo)**: Marcar Audiência, Partes,
Visualizar, Movimentar — todos habilitados; "Modificar Dados" aparece **desabilitado/acinzentado**
para esse perfil (ainda não testei quem consegue usá-lo — provavelmente Serventia/Cartório ou
Admin, a confirmar).

---

## Capturas de tela adicionais (rodada 5)

| ID | Arquivo | Conteúdo |
|---|---|---|
| IMG-15 | `img_15_aluno_processo_vinculado.png` | Área do Aluno da Mariana, já com o processo 0000001-74.2026.8.26.0001 listado em "Processos Vinculados" |
| IMG-16 | `img_16_detalhe_processo_dados.png` | Tela de detalhe do processo — Autos, Dados do Processo (polos, vara, classe, status) |
| IMG-17 | `img_17_opcoes_processo_menu.png` | Menu "Opções Processo" aberto (Marcar Audiência, Partes, Visualizar, Modificar Dados desabilitado, Movimentar) |
| IMG-18 | `img_18_eventos_processo_movimentacao.png` | Aba "Eventos do Processo" mostrando a timeline com Protocolo da Petição Inicial + Juntada de Documentos |

---

## Pendências atualizadas

- Reatribuir (ou não) o campo "coordenador" do ciclo pra Camila, via tela de editar ciclo.
- Testar login da Camila (Professor) e documentar pra onde ela é redirecionada.
- Distribuir um processo fictício pro ciclo/grupo, pra Mariana ter algo em "Processos Vinculados".
- Investigar a origem dos números fixos do "Resumo do Semestre" antes de usá-los em qualquer texto
  do manual.
- Confirmar se "Consultar Todos" (submenu Processos) e "Audiências" (menu superior do Aluno) são
  funcionalidades ainda não implementadas (href="#") ou erro de link — não documentar como prontas
  até confirmar.
- Escrever a seção da Área do Aluno **com** processo distribuído (movimentações, documentos,
  avaliações reais), depois de cadastrar um processo de teste pelo fluxo "Cadastrar Processos".
- Testar "Marcar Audiência" (opção disponível no menu do processo, ainda não testada).
- Testar login como Juiz/Serventia/MP para ver quais tipos de movimentação aparecem pra eles (hoje
  só vimos "Juntada de Documentos", disponível pro Advogado/Aluno) e quem consegue usar "Modificar
  Dados" (aparece desabilitado para o Aluno/Advogado).
- Atualizar o capítulo do Professor com "Distribuir Novo Processo"/"Relatório de Notas" usando este
  processo de teste já cadastrado.
- Escrever a seção "Como Movimentar um Processo" no manual, usando a movimentação de teste já
  registrada (Juntada de Documentos) como exemplo verificado.

## Rodada 6: vínculo aluno↔grupo, 2º grupo em processo, documentos, editor, avaliação, notificações, bloqueio

### Novos usuários fictícios cadastrados

| Nome | E-mail | Senha | Perfil | Grupo | Cargo |
|---|---|---|---|---|---|
| Rafael Souza Martins | rafael.martins@exemplo.com | Simu@Teste2026 | Aluno | Cartório Distribuidor de Formosa | Serventia/Cartório |

(Lucas Andrade Monteiro já existia da rodada 5 — aprovado nesta rodada como Aluno/Ativo.)

### Novo Grupo de Trabalho criado

| Nome | Cargo Simulação | Ciclo |
|---|---|---|
| Monteiro & Advogados Associados | Advogados Polo Passivo | NPJ Cível 2026/2 |
| Cartório Distribuidor de Formosa | Serventia/Cartório | NPJ Cível 2026/2 |

### Achado importante: como vincular um 2º grupo a um processo existente

Não existe essa ação nem no Professor, nem nos grupos de advogados. É uma ação exclusiva de quem
pertence a um grupo com cargo **Serventia/Cartório**, feita pela **Área do Aluno** desse usuário
(view `processos:atribuir_grupo_processos`, POST para `/processos/api/atribuir-grupo/`). Por isso
foi necessário criar o aluno fictício Rafael Souza Martins e o grupo "Cartório Distribuidor de
Formosa" só para testar esse fluxo. Documentado na seção 12 do Capítulo do Aluno
("Papel de Serventia/Cartório (SC): Vincular um Grupo a um Processo").

Confirmado: a seleção de grupos no modal "Atribuir Grupo ao Processo" é **aditiva** (marcar um novo
grupo não desmarca os já vinculados). Só existe "Remover atribuição", que desvincula todos de uma
vez. Depois de vincular o grupo Serventia/Cartório, o campo "Serventia" do processo foi preenchido
automaticamente com o nome do grupo e o status mudou de "Protocolado" para "Autuado".

### Arquivo fictício criado para testes de anexo

Criado com pandoc + xelatex: `assets/arquivos-exemplo/procuracao_ficticia.pdf` (Procuração Ad
Judicia fictícia, ~26KB, conteúdo claramente marcado como "documento fictício" e "sem validade
jurídica real", para não ser confundido com um modelo real por quem for reaproveitar o manual).

### Movimentações de teste registradas no processo 0000001-74.2026.8.26.0001

| Nº | Tipo | Usuário | Descrição | Arquivo |
|---|---|---|---|---|
| 3 | Autuação e Distribuição | Rafael Souza Martins | Grupos atribuídos ao processo | — |
| 4 | Juntada de Documentos | Lucas Andrade Monteiro | Juntada de procuração ad judicia (upload de arquivo) | procuracao_ficticia.pdf |
| 5 | Juntada de Documentos | Lucas Andrade Monteiro | Contestação via editor on-line, assinada eletronicamente | contestacao_ficticia.html |

### Avaliação de teste

Professor Camila Ferreira Duarte avaliou a movimentação nº 5 (Lucas): **nota 9,0**, com comentário
visível ao aluno. Confirmado que a nota aparece corretamente em "Minhas Notas" do Lucas (Média
Geral 9,00, Avaliadas 1 de 2, Melhor Nota 9,0).

### Notificações — achados

- Aluno recebe notificação para: inclusão no ciclo, grupo vinculado a um processo, nova
  movimentação em processo vinculado.
- Professor recebe notificação ao ser designado coordenador de um ciclo (rodada anterior).
- **Atribuir uma nota NÃO gera notificação** para o aluno avaliado — só aparece em "Minhas Notas".
- **Uma nova movimentação de um aluno NÃO gerou notificação visível para o Professor** responsável
  pelo ciclo (testado logo após a movimentação nº 5 — nenhuma notificação nova no sino da Camila).

### Bloqueio/desativação de cadastro — achados

Testado com Rafael Souza Martins, via Professor (Gerir Usuários → editar → desmarcar "Ativo" →
Salvar). Resultado:

- O usuário **não fica com status "Inativo"** — ele volta a aparecer na aba "Pendentes" da Gestão
  de Usuários, como se nunca tivesse sido aprovado.
- Ao tentar logar com a senha correta, recebe a mensagem genérica "Por favor, entre com um usuário
  e senha corretos." — o sistema não avisa que a causa é o cadastro estar bloqueado.
- Professor só pode fazer isso com cadastros do tipo Aluno (mesma regra de
  `tipos_que_pode_atribuir()`).

### Capturas de tela desta rodada

| Arquivo | Conteúdo |
|---|---|
| img_19_aluno_aprovado_gestao_usuarios.png | Lucas aprovado como Aluno/Ativo na lista "Todos os Usuários" |
| img_20_grupo_criado_membro_adicionado.png | Grupo "Monteiro & Advogados Associados" com Lucas como membro |
| img_21_processo_tres_grupos_vinculados.png | Processo com 3 grupos vinculados, status "Autuado" |
| img_22_movimentacao_documento_anexado.png | Upload de arquivo incluído na lista "Documentos a Anexar" |
| img_23_evento_visualizar_baixar_documento.png | Evento expandido com botões Visualizar/Baixar |
| img_24_editor_online_documento_assinado.png | Editor on-line com bloco "ASSINADO ELETRONICAMENTE" |
| img_25_avaliacao_nota_feedback.png | Formulário de avaliação preenchido (nota 9,0) |
| img_26_aluno_minhas_notas.png | "Minhas Notas" do Lucas já com nota real |
| img_27_notificacoes_aluno.png | Página de notificações completa do Aluno |
| img_28_notificacao_professor.png | Notificação de designação como coordenador (Professor) |
| img_29_usuario_desativado_pendente.png | Rafael voltando a "Pendente" após desmarcar Ativo |
| img_30_login_bloqueado.png | Login rejeitado para o usuário desativado |

## Investigação: "Resumo do Semestre" (painel administrativo)

**Achado confirmado por leitura de código** (`acesso/templates/acesso/painel_administrativo.html`
L527-545 e `acesso/views_admin_usuarios.py::painel_administrativo`, L81-201):

Os 4 cartões de KPI do bloco "Resumo do Semestre (Atual)" (coluna direita do painel
administrativo) são **números fixos ("hardcoded") no template**, e não refletem dados reais do
sistema:

```
{% include 'base/components/_card_kpi.html' with rotulo="Processos Ativos" numero=45 only %}
{% include 'base/components/_card_kpi.html' with rotulo="Avaliações Pendentes" numero=12 variante="alerta" only %}
{% include 'base/components/_card_kpi.html' with rotulo="Grupos de Trabalho" numero=8 only %}
{% include 'base/components/_card_kpi.html' with rotulo="Alunos Vinculados" numero=20 only %}
```

Curiosamente, a view **calcula** pelo menos um número real equivalente —
`context["total_alunos_vinculados"]` (contagem real de alunos ativos vinculados a ciclos "em
andamento") — mas esse valor nunca é usado no template; o cartão "Alunos Vinculados" sempre mostra
"20", não importa quantos alunos existam de fato. Os outros três cartões (Processos Ativos,
Avaliações Pendentes, Grupos de Trabalho) não têm nem cálculo correspondente na view — são
puramente decorativos.

**Conclusão para o manual**: esse bloco deve ser documentado como **dados de exemplo/placeholder,
não conectados ao sistema real** — os números NÃO mudam conforme o uso da plataforma. Não é um bug
de exibição de um valor errado; é conteúdo estático que nunca foi ligado a uma fonte de dados.

Também confirmado nessa mesma leitura: dos 4 botões de "Ações Rápidas" (mesma coluna), apenas
"Gerir Usuários" tem função real (abre o modal de usuários). "Distribuir Novo Processo", "Agendar
Audiência" e "Relatório de Notas" são `<a href="#">` sem nenhum `onclick`/JS associado — confirma o
achado anterior de que são funcionalidades não implementadas.

## Pendências atualizadas (rodada 6)

- Testar "Marcar Audiência" (ainda não testado).
- Testar login como Juiz/Serventia/MP para ver quais tipos de movimentação aparecem e quem usa
  "Modificar Dados".
- "Distribuir Novo Processo", "Agendar Audiência" e leitura do "Relatório de Notas" consolidado do
  Professor — ainda não testados.
- Confirmar se "Consultar Todos" (submenu Processos) e "Audiências" (menu superior) são
  funcionalidades pendentes ou erro de link.
- Botão "Devolver para Revisão" da avaliação — ainda não testado.
- Capítulos de Serventia/Cartório, Ministério Público e Juiz — ainda não escritos.
- 3 âncoras órfãs pré-existentes no Índice (`apos-cadastro`, `como-fazer-login`,
  `redirecionamento`) — não introduzidas nesta rodada, mas ainda pendentes de correção.
## Rodada 7: revisão de pendências "para depois" após mudança de pasta

Depois de mover `manual-usuario/` para a raiz do repositório, o usuário pediu para reler o
documento em busca de trechos deixados "para depois" e nunca atualizados. Achados e correções
desta rodada (só correções de conteúdo/texto do manual, nenhuma alteração de código):

1. **Glossário**: tinha nota "será expandido... assim que a Seção 3.2 do roteiro for totalmente
   confirmada". Confirmado via `scripts/seed_pos_migracao.py` (CARGOS = SC/APA/APP/MP/JZ, batendo
   com o comentário em `ciclos/models.py`) — adicionados os 5 termos ao glossário.
2. **Introdução**: estava literalmente `*(a escrever)*`. Escrita do zero (objetivo do simulador,
   conceitos centrais: Ciclo de Simulação, Grupo de Trabalho, Processo, Movimentação).
3. **"Resumo do Semestre" / "Ações Rápidas"** (Capítulo do Admin, seção 1): documentado o achado já
   registrado na Rodada 6 sobre os números fixos (45/12/8/20) e os 3 links mortos, com referência
   cruzada nos capítulos do Coordenador e do Professor em vez de duplicar o texto.
4. **"Consultar Todos" e menu "Audiências"** (Capítulo do Aluno): removida a ressalva "confirmar se
   é intencional" — confirmado por código (`base/templates/base/components/_nav_secundaria.html`,
   ambos `href="#"`) que são definitivamente não implementados, não uma dúvida de permissão.
5. **"Marcar Audiência"** no menu "Opções Processo": adicionada nota de que, apesar de parecer
   habilitado visualmente, não tem nenhuma ação por trás (mesma limitação do item acima).
6. **Referência cruzada stale**: o item "Cadastrar Processos" do menu "Processos" apontava para
   "documentar em detalhe assim que um processo de teste completo for cadastrado" — mas a seção 7
   ("Como Cadastrar um Processo") já existe e cobre isso. Corrigido para link direto.
7. **Índice quebrado**: o editor local do usuário aparentemente regenerou automaticamente o bloco
   "## Índice" no formato de TOC do GitHub/VS Code (âncoras tipo `#7-como-cadastrar-um-processo`),
   que não batem com as âncoras reais (`<a name="...">`) usadas no resto do documento — quase todos
   os links do índice ficaram quebrados. Restaurado para o formato funcional anterior (lista
   numerada com âncoras manuais).
8. **3 âncoras órfãs corrigidas**: `apos-cadastro`, `como-fazer-login` e `redirecionamento` (headings
   "O que Acontece Logo Após o Cadastro", "Como Fazer Login", "Para onde Cada Perfil é
   Redirecionado") não tinham `<a name>` correspondente — adicionado. Validado por script que **zero**
   links internos `[...](#...)` do manual ficam sem âncora correspondente agora.
9. **"Última atualização"** no cabeçalho do manual: atualizada de 2026-09-17 para 2026-09-19.

**Nova pendência encontrada** (apontada pelo usuário): a seção "3. Como Fazer Login" não tem
nenhuma captura de tela — só texto. Faltando print da tela de login "limpa" (sem erro); as imagens
existentes (img_04) só cobrem o caso de erro de login. Marcado inline no manual com 🖼️ **Pendente**.

## Pendências atualizadas (rodada 7)

- Capturar screenshot da tela de login limpa (sem erro) para a seção "Como Fazer Login".
- Testar "Marcar Audiência" (ainda não testado) — já documentado como não implementado, mas não
  custa reconfirmar quando os capítulos de Juiz/Serventia/MP forem escritos.
- Testar login como Juiz/Serventia/MP para ver quais tipos de movimentação aparecem e quem usa
  "Modificar Dados".
- Botão "Devolver para Revisão" da avaliação — ainda não testado.
- Capítulos de Serventia/Cartório, Ministério Público e Juiz — ainda não escritos.
- Confirmar se o editor local do usuário (extensão de VS Code?) vai regenerar o índice de novo
  automaticamente — se sim, considerar desativar a extensão de auto-TOC para esse arquivo, já que
  ela usa um formato de âncora incompatível com o resto do documento.
## Rodada 8: correções pontuais pedidas pelo usuário + testes de redirecionamento

Correções de estilo/tom pedidas pelo usuário (manual deve soar como manual, não como relatório de
QA — sem "confirmado por leitura de código", "confirmado nesta verificação" etc.):

1. **"Como Fazer Login"**: adicionado print da tela de login limpa (`img_31_login_tela_limpa.png`).
2. **"Para onde Cada Perfil é Redirecionado"**: reescrita. Agrupei Admin/Coordenador/Professor (
   mesmo destino, Painel de Controle) e separei o Aluno (dois casos: sem vínculo / já vinculado).
   Testes feitos nesta rodada para fechar a lacuna:
   - Login como **Mariana** (Aluno já vinculado ao grupo "Albuquerque & Associados") → redireciona
     direto para `/processos/area-servidor/` (Área do Aluno), já com o processo vinculado listado.
     Print: `img_32_aluno_redirecionado_area_aluno.png`.
   - Login como **Camila** (Professor) → redireciona para `/acesso/painel-administrativo/`, tela
     **visualmente idêntica** à do Admin/Coordenador. Print: `img_33_professor_redirecionado_painel.png`.
3. **Admin > "Painel de Controle"**: removida a menção a "confirmado por leitura de código" —
   mantido só o fato (números fixos, 3 dos 4 atalhos não implementados), em tom de manual.
4. **Admin > "Como Aprovar um Cadastro Pendente"**: removido o "Pré-requisito"; adicionada
   observação de que as opções de Tipo de Perfil mostradas dependem da permissão de quem está
   logado (Admin vê 4 opções, Coordenador/Professor veem menos).
5. **Capítulo do Coordenador**: removida a menção "única diferença confirmada nesta verificação" —
   mantida só a diferença em si (não pode atribuir perfil Admin), em tom de manual.

Novas imagens desta rodada: `img_31_login_tela_limpa.png`, `img_32_aluno_redirecionado_area_aluno.png`,
`img_33_professor_redirecionado_painel.png`.

Validação: script conferindo `<a name>` vs. links internos e existência de todas as imagens
referenciadas — zero âncoras e zero imagens faltando.
## Rodada 9: aluno vinculado a mais de um ciclo (multi-ciclo)

Pergunta do usuário: quando o Aluno está vinculado a mais de um ciclo, ele escolhe em qual entra
primeiro? E como troca de ciclo depois? Resposta obtida por leitura de código
(`ciclos/middleware.py::CicloAtivoMiddleware`, `ciclos/views.py::selecionar_ciclo`/`ativar_ciclo`,
`ciclos/permissions.py::pode_trocar_ciclo_ativo`) e confirmada com teste ao vivo:

- Criado um segundo ciclo, **"NPJ Penal 2026/2"** (1º semestre/2026), coordenado pela Camila.
- Criado o grupo **"Duarte & Advogados Criminalistas"** (Advogados Polo Ativo) nesse ciclo, e
  adicionada a Mariana (que já estava no grupo "Albuquerque & Associados" do ciclo "NPJ Cível
  2026/2").
- Login da Mariana com os 2 ciclos ativos → **tela "Selecione o Ciclo"** (`/ciclos/selecionar/`),
  listando os dois, cada um levando à Área do Aluno normalmente depois de escolhido.
- Depois de escolhido, aparece um seletor no cabeçalho (ícone de seta circular, ao lado do nome do
  usuário) que permite **trocar de ciclo ativo** a qualquer momento sem logout — confirmado que
  esse seletor só aparece pro Aluno (`pode_trocar_ciclo_ativo`: Admin/Coordenador/Professor não
  usam, porque o Painel deles já mostra todos os ciclos de uma vez).
- Com exatamente 1 ciclo ativo, a escolha é automática/transparente (não aparece a tela de seleção).

Conteúdo já incorporado à seção "4. Para onde Cada Perfil é Redirecionado" do manual, com prints
novos: `img_34_selecionar_ciclo.png`, `img_35_trocar_ciclo_dropdown.png`.

**Nota**: ao reler o arquivo para validar, o índice do `MANUAL_DO_USUARIO.md` tinha sido
regenerado de novo pelo editor local do usuário no formato auto-TOC quebrado (mesmo problema da
Rodada 7) — restaurado outra vez. Isso já aconteceu 2x nesta sessão; recomendo fortemente
desativar a extensão de auto-TOC do editor para este arquivo específico, ou pelo menos configurá-la
para não rodar automaticamente ao salvar.

## Rodada 10: correções explícitas do usuário (linguagem de manual, não de relatório técnico)

Lista de correções pedidas pelo usuário, todas aplicadas:

1. Professor > "3. Como Avaliar uma Movimentação": removida a frase "esse fluxo ainda não foi
   testado em detalhe" do botão "Devolver para Revisão" → substituída por nota
   "(Seção em elaboração)".
2. Removida a nota sobre o contador "Avaliações Pendentes" do Resumo do Semestre do Professor →
   "(Seção em elaboração — parte em desenvolvimento)".
3. Removida por completo a nota sobre "Desmarcar Ativo não cria status Inativo separado" (é um bug
   do sistema, não deve ser documentado como comportamento esperado).
4. Removida a referência à função interna `tipos_que_pode_atribuir()` da nota sobre bloqueio de
   cadastro pelo Professor — reescrita sem expor nomes de função/classe do código.
5. Nota final do capítulo do Professor (sobre Distribuir Novo Processo/Agendar Audiência/Relatório
   de Notas) substituída por "(Seção em elaboração — em desenvolvimento do código)".
6. Aluno > "3. Menu Processos": adicionado print (`img_36_aluno_menu_processos_dropdown.png`);
   removida também a menção a "confirmado por leitura de código" do item "Consultar Todos".
7. Aluno > "4. Menu Audiências": reescrita por completo, removendo toda menção a links quebrados,
   arquivos de código ou internals do backend → "(Seção em elaboração — funcionalidade em
   desenvolvimento)".
8. "5. Minhas Notas" e "6. Notificações": adicionadas âncoras `<a name>` no padrão do resto do
   documento (estavam sem âncora própria, causando o índice quebrado — ver item 10 abaixo).
9. "7. Como Cadastrar um Processo": adicionado um print por passo (Passo 1: dados,
   `img_37_cadastro_passo1_dados.png`; Passo 2: documentos, `img_38_cadastro_passo2_documentos.png`;
   Passo 3: resumo, `img_39_cadastro_passo3_resumo.png`).
   **Achado importante**: testado ao vivo e confirmado que o Passo 2 (Documentos) do Cadastro de
   Processo **não tem** a aba "Modelos, Editor On-line" — só um upload de arquivo simples. Essa aba
   só existe no fluxo de Movimentar Processo (seção 10/11). Não foi documentada no Passo 2 porque
   não existe ali; reportado ao usuário em vez de presumir que fosse uma omissão do manual.
10. Índice: estava novamente no formato auto-TOC quebrado do editor local (3ª ocorrência do mesmo
    problema das Rodadas 7 e 9) — todo o bloco "## Índice" foi reconstruído manualmente com as
    âncoras corretas (`<a name="...">`) e validado por script (32 âncoras definidas = 32
    referenciadas, 0 faltando; 39 imagens referenciadas, 0 faltando).
11. Nota "Opções Processo" (Aluno > Detalhe do Processo): removida a comparação/comentário sobre
    inconsistência visual de "Marcar Audiência" → apenas descreve o menu e sinaliza
    "(Seção em elaboração)" para a ação ainda não implementada.
12. Nota sobre tipos de movimentação (Aluno > 9.): removido o trecho "ainda não confirmado; ver
    capítulos desses perfis quando forem escritos".
13. Todas as ocorrências de "ainda não testada em detalhe" (e variações) trocadas por
    "(Seção em elaboração)", incluindo uma instância adicional encontrada na seção 10 (aba
    "Navegação de Arquivo") que o usuário não citou explicitamente mas seguia o mesmo padrão.
14. Travessões ("—") removidos em todo o documento (71 ocorrências), substituídos por dois-pontos,
    vírgula, ponto e vírgula ou parênteses conforme o sentido de cada frase. Mantida apenas 1
    ocorrência legítima: a citação literal do caractere "—" que a própria interface do sistema
    mostra como placeholder (seção "Minhas Notas").

Nenhuma alteração foi feita além do que foi pedido explicitamente. Uma lista separada de possíveis
melhorias adicionais (mesmo padrão de linguagem de verificação/teste, ex.: "Testado com um Aluno
do grupo..." na seção 9, "nesta rodada de testes" na seção de Notificações do Sistema) foi
levantada e reportada ao usuário para aprovação prévia, sem aplicar nada.

**Atualização Rodada 10**: usuário revisou e aprovou remover o framing de teste também nos dois
trechos extras identificados (seção 9 do Aluno e "Notificações do Sistema") — ambos ajustados para
manter só o fato observado, sem "testado com..."/"nesta rodada de testes".

## Rodada 11: investigação de "Devolver para Revisão" + descoberta da mudança de escala (nota → estrelas)

Pedido do usuário: ler o código de "Devolver para Revisão" para entender o fluxo antes de
documentar. Leitura de `avaliacoes/views.py`, `avaliacoes/models.py`, `avaliacoes/estrelas.py`,
`movimentacoes/models.py` e `movimentacoes/services.py`.

**Achado 1 (reportado e confirmado com o usuário): "Devolver para Revisão" não é um fluxo
completo.** O botão só grava um `FeedbackProfessor` com `nota=None` e o comentário preenchido —
não existe nenhum campo de status na movimentação, nenhuma notificação específica é disparada
(consistente com o que o manual já documentava sobre notificações de avaliação) e, na tela "Minhas
Notas" do aluno, o registro aparece igual a qualquer avaliação sem nota, sem nenhum selo de
"revisão solicitada". Existe uma correção de movimentação ("Emenda/Retificação", com nova versão
`movimentacao_origem`), mas é um mecanismo totalmente independente do botão "Devolver para
Revisão" (depende só de não haver ainda outra movimentação encadeada sobre a original). Decisão do
usuário: manter a seção como "(Seção em elaboração)", sem tentar descrever um fluxo que não existe
de fato.

**Achado 2 (não perguntado, descoberto durante a investigação): a interface de avaliação mudou de
"Nota (0 a 10)" para estrelas (1 a 5).** Confirmado ao vivo: a escala interna no banco continua
0–10 (`avaliacoes/estrelas.py`: 1★ = 2 pontos, 5★ = 10 pontos, conversão centralizada só ali), mas
o formulário do Professor (`avaliacoes/templates/avaliacoes/avaliar.html`) e a tela "Minhas Notas"
do Aluno agora usam só estrelas. Testado ao vivo (login como Camila/Professor avaliando uma
movimentação de Mariana com 4 estrelas, depois login como Mariana conferindo o resultado em
"Minhas Notas"). Manual atualizado:

- Professor > "3. Como Avaliar uma Movimentação": reescrita para descrever o campo de estrelas (1
  a 5) em vez de nota numérica, e para mencionar a nova página dedicada **"Avaliações Pendentes"**
  (`/avaliacoes/pendentes/`) como caminho alternativo de acesso (descoberta também durante o teste:
  não existia antes, tem filtro por ciclo e contadores de pendentes/alunos aguardando/mais antiga).
  Print antigo (`img_25`, com "nota 9,0" na interface antiga) substituído por
  `img_40_professor_avaliar_estrelas.png`.
- Aluno > "5. Minhas Notas": indicadores descritos como estrelas de 1 a 5 em vez de nota numérica.
  Print antigo (`img_26`) substituído por `img_41_aluno_minhas_notas_estrelas.png`.

**Achado 3 (à parte, não documentado ainda — para revisão futura): o Painel de Controle do
Professor hoje mostra um card "Avaliações Pendentes" com número real e calculado (visto: 14 → 13
depois de avaliar uma movimentação), não mais um valor fixo no template como constatado em rodadas
anteriores. Vale revisar se a seção "Admin > 1. Painel de Controle" (que descreve o mesmo painel
compartilhado) ainda reflete o comportamento atual antes de fechar essa parte do manual.

Validação final: 32 âncoras / 32 referências, 39 imagens / 0 faltando, 1 travessão remanescente
(citação literal do placeholder "—" da interface), 760 linhas.

## Rodada 12: revisão geral do que já estava documentado contra o código atual

Pedido do usuário: "atualize tudo que já foi documentado e teve alteração no código". Levantamento
via `git log --oneline --since=2026-09-19` no repositório principal (fora `manual-usuario/`): 50
commits desde a última rodada de testes. Revisão cruzada de cada commit contra o texto já escrito
no manual; mudanças aplicadas:

1. **Admin/Coordenador/Professor > "1. Painel de Controle"**: reescrito. O "Resumo do Semestre"
   (agora "Resumo dos Ciclos Ativos" no próprio sistema) mostra números reais e calculados
   (`d3ddb89`, `4ed2fb8`), confirmado ao vivo (Avaliações Pendentes caiu de 14 para 13 depois de
   uma avaliação). As "Ações Rápidas" agora têm só 3 botões, todos funcionais: **Relatório de
   Notas**, **Gerir Usuários**, **Avaliações Pendentes** — "Distribuir Novo Processo" e "Agendar
   Audiência" não existem mais na tela (`ba98095`). Adicionadas duas subseções novas com prints:
   Relatório de Notas (`/avaliacoes/relatorio-notas/`) e Avaliações Pendentes
   (`/avaliacoes/pendentes/`). Prints novos: `img_42_painel_controle_resumo_real.png`,
   `img_43_relatorio_notas.png`, `img_44_avaliacoes_pendentes.png`.
2. **"4. Para onde Cada Perfil é Redirecionado"**: "Resumo do Semestre" → "Resumo dos Ciclos
   Ativos" (só o nome do bloco, para bater com a tela).
3. **"1. Como se Cadastrar no Sistema"**: adicionado o passo 4 (novo) — caixa obrigatória "Li e
   aceito os Termos de Uso e a Política de Privacidade" (`c10a0d4`), confirmada ao vivo na tela de
   cadastro. `img_01_cadastro_vazio.png` recapturado para mostrar a caixa.
4. **"3. Como Fazer Login"**: adicionada nota sobre o portão de reaceite de Termos de Uso que pode
   aparecer logo após o login para contas já existentes, quando a versão dos termos muda — vivido
   ao vivo duas vezes nesta sessão (Camila e Mariana), tela "Atualização dos Termos de Uso"
   (`acesso/aceite-termos/`).
5. **Aluno > "12. Papel de Serventia/Cartório (SC)"**: reescrito por completo. O fluxo mudou de
   "um processo por vez, sem remoção individual" para: seleção em lote de vários processos por
   checkbox (+ botão "Atribuir grupo aos selecionados"), remoção individual de um grupo específico
   por um ícone de lixeira no próprio card (com confirmação), e o botão "Desvincular Grupos"
   (renomeado, `d5bc2db`) continua existindo como remoção total separada
   (`c875765`, `ac8c429`, `8972aed`, `2e4fde5`, `3251b55`). Também documentado que a atribuição
   gera sozinha um evento "Autuação e Distribuição" ou "Redistribuição" (tipo novo,
   `30b385b`/`2353498`) na aba Eventos do Processo. Não foi possível gravar prints novos do modal
   atualizado nesta rodada (usuário de teste do grupo Serventia/Cartório, Rafael Souza Martins, não
   tinha a senha padrão de teste) — a reescrita foi feita só por leitura de código
   (`processos/templates/processos/pagina_aluno.html`), sem confirmação visual ao vivo. Fica como
   pendência: testar e capturar prints reais desse fluxo numa próxima rodada.

Commits revisados e descartados por não afetarem texto já documentado (mudança interna, correção
de segurança sem efeito visível, ou funcionalidade nova ainda não escrita no manual): correção de
regex de nome acentuado no JS de cadastro (`330c727`), correção de open redirect em
`selecionar_ciclo` (`0889126`), páginas de erro customizadas (`6e6f06c`), tela "Minha Conta"/
redefinição de senha (`989e7ce`, nova funcionalidade ainda não documentada, não "já documentada").

Validação final: 32 âncoras / 32 referências, 42 imagens / 0 faltando, 1 travessão remanescente
(citação literal do placeholder "—" da interface), 794 linhas.


## Rodada 13: Prints atualizados - Cadastro com Termos de Uso

**Solicitação:** atualizar com prints reais a seção "1. Como se Cadastrar no Sistema", refletindo o novo checkbox obrigatório de aceite dos Termos de Uso e Política de Privacidade (adicionado na Rodada 12 apenas como texto).

**Teste ao vivo realizado:**
- Usuário fictício de teste criado: Beatriz Nogueira Campos (beatriz.ncampos@exemplo.com, senha Simu@Teste2026).
- Navegado para `/acesso/cadastro/`, preenchidos Nome Completo, Email, Senha, Confirmação de Senha e marcada a checkbox "Li e aceito os Termos de Uso e a Política de Privacidade do Simulador Projudi.".
- Submissão via "CRIAR USUÁRIO" confirmada com sucesso: mensagem verde "Cadastro realizado com sucesso! Aguarde a aprovação de um responsável para acessar o sistema."
- Observação: uma primeira tentativa de e-mail (beatriz.campos@exemplo.com) já havia sido cadastrada em teste anterior (erro "Usuário com este Email já existe."), por isso o cadastro final de confirmação usou o e-mail beatriz.ncampos@exemplo.com.

**Imagens atualizadas (mesmos nomes de arquivo, substituídas em `assets/`):**
- `img_01_cadastro_vazio.png` - formulário em branco com a checkbox de Termos de Uso visível. **Correção:** a versão commitada na Rodada 12 estava, na verdade, desatualizada (print antigo, sem a checkbox e com e-mail de suporte antigo). Recapturada e substituída nesta rodada apos o usuario apontar o problema.
- `img_02_cadastro_preenchido.png` - formulário preenchido com todos os campos e checkbox marcada.
- `img_03_cadastro_sucesso.png` - tela de confirmação com a mensagem de sucesso.

**Validação pós-edição:** script de checagem de âncoras/links internos (0 ausentes), referências de imagens em `assets/` (42 referências, todas existentes em disco) e contagem de travessões (1, o placeholder literal já conhecido na seção "Minhas Notas") - todos OK.

Nenhuma alteração de texto foi necessária no MANUAL_DO_USUARIO.md nesta rodada, apenas substituição das imagens (os nomes de arquivo já estavam referenciados corretamente desde a Rodada 12).


## Rodada 14: Verificação de Editar/Excluir Grupo e Adicionar/Remover Aluno

**Solicitação:** verificar se existe (e como funciona) a possibilidade de alterar, inserir e
remover grupos de um ciclo, e adicionar/remover alunos dos grupos - sessão comum a Admin,
Coordenador e Professor.

**Verificação no código (`ciclos/views.py`, `ciclos/urls.py`, `ciclos/forms.py`,
`ciclos/permissions.py`, `ciclos/templates/ciclos/gerenciar_grupos.html`):**
- `gerenciar_grupos`: mesma view cuida de criar E editar grupo (reusa `GrupoTrabalhoForm`; se o
  POST trouxer `grupo_id`, edita; senão, cria).
- `adicionar_membro` / `remover_membro`: endpoints AJAX próprios, JSON, sem tela de confirmação no
  remover.
- `pode_gerenciar_grupos_ciclo`: Admin sempre, Coordenador sempre, Professor somente se for
  responsável (coordenador) do ciclo ou participante - confirma que é a mesma tela/permissão para
  os três perfis de gestão.
- **Não existe** nenhuma view, URL ou botão para excluir um Grupo de Trabalho inteiro. Busca por
  "excluir/deletar/delete" nesses arquivos não retornou nada.

**Teste ao vivo realizado** (login como Camila Ferreira Duarte, Professor/Coordenador do ciclo NPJ
Cível 2026/2):
1. Editar grupo: clicado no ícone de lápis do grupo "Albuquerque & Associados" -> modal "Editar
   Grupo" abriu com Nome e Papel pré-preenchidos -> cancelado (não quis alterar dados reais do
   ciclo).
2. Remover aluno: clicado no ícone de lixeira ao lado de "Mariana Albuquerque Teixeira" -> removida
   imediatamente do grupo, sem confirmação, com toast de sucesso -> **re-adicionada em seguida**
   (via "+ADD" na lista "Alunos sem Grupo") para restaurar o estado original dos dados de teste.
3. Confirmado visualmente: nenhum ícone/botão de exclusão de grupo em nenhum lugar da tela.

**Atualização no manual:** seção 4 do Capítulo do Admin (`admin-criar-grupo`) reescrita e
renomeada para "Como Criar, Editar e Excluir um Grupo de Trabalho, e Adicionar/Remover Alunos",
cobrindo os 4 fluxos (criar, editar, adicionar aluno, remover aluno) com prints novos
(`img_45_grupo_editar_modal.png`, `img_46_grupo_aluno_removido.png`) e um aviso explícito de que
**não existe exclusão de grupo inteiro**. Título no Índice atualizado. Frase-resumo do Capítulo do
Coordenador (que reaproveita os passos do Admin) atualizada para mencionar editar/remover. Seção 2
do Capítulo do Professor ganhou um parágrafo apontando para os novos fluxos de editar/remover.

**Validação pós-edição:** âncoras (0 ausentes), imagens (44 referências, todas existentes),
travessões (1, o placeholder já conhecido) - todos OK.


## Rodada 15: Nova Funcionalidade "Alterar Senha" + Redefinição de Senha por Admin + Validação ao Vivo da Seção SC (12)

**Solicitação:** documentar a nova funcionalidade de troca de senha pelo próprio usuário
("Minha Conta"), e seguir com o roteiro pendente (que incluía redefinir a senha do Rafael para
validar ao vivo a seção 12).

**1. Nova seção "Como Alterar sua Senha (Minha Conta)" (Primeiros Passos, seção 5):**
- Código: `acesso/views.py::minha_conta` + `AlterarMinhaSenhaForm` (`acesso/forms.py`, baseado em
  `PasswordChangeForm` do Django). Acessível a qualquer perfil logado via ícone de cadeado no
  cabeçalho (`base/templates/base/base.html`).
- Teste ao vivo com Camila: troquei a senha dela para "Simu@Teste2027", confirmei a mensagem
  "Senha alterada com sucesso." e que **a sessão não caiu** (`update_session_auth_hash`), depois
  **revertida** para "Simu@Teste2026" (senha padrão de teste) na sequência.
- 3 prints novos: `img_47_minha_conta_vazio.png`, `img_48_minha_conta_preenchido.png`,
  `img_49_minha_conta_sucesso.png`.

**2. Descoberta lateral: redefinição de senha por Admin/Coordenador/Professor (`AtualizarUsuarioForm`,
`acesso/forms_admin_usuarios.py`):** o modal "Editar/Aprovar Usuário" (já documentado na seção 2 do
Capítulo do Admin) tem uma subseção colapsável **"Alterar Senha"** com campos "Nova Senha" e
"Confirmação", **antes não documentada**. Usei exatamente essa funcionalidade real do sistema (não
uma alteração de código) para redefinir a senha do Rafael Souza Martins para "Simu@Teste2026",
resolvendo o bloqueio que impedia testar a seção 12 ao vivo desde a Rodada 12. *(Ainda não escrevi
uma seção própria no manual para esse recurso de "Admin redefine a senha de outro usuário" — fica
como pendência para a próxima rodada, junto com os capítulos que faltam.)*

**3. Validação ao vivo da seção 12 (SC: vincular grupo a processo), antes só baseada em código:**
- Login como Rafael Souza Martins (Cartório Distribuidor de Formosa, ciclo NPJ Cível 2026/2) —
  primeiro login dele nesta bateria de testes, passou pela tela "Atualização dos Termos de Uso"
  (aceite obrigatório), confirmando também essa feature.
- Abri o modal "Atribuir Grupo ao Processo" pelo ícone de pessoas: confirma exatamente a descrição
  já escrita (cartões por grupo, etiqueta "Já Vinculado", ícone de lixeira, botão "Desvincular
  Grupos", "Confirmar Atribuição").
- Cliquei na lixeira do grupo "Monteiro & Advogados Associados": apareceu a confirmação "Remover o
  grupo 'Monteiro & Advogados Associados' deste processo? Sim/Não" — exatamente como documentado.
  Cliquei em **Não** para não alterar os dados de teste reais.
- 2 prints novos adicionados à seção 12: `img_50_sc_atribuir_grupo_modal.png`,
  `img_51_sc_remover_grupo_confirmacao.png`.
- Não testei a seleção em lote (checkbox + "Atribuir grupo aos selecionados") nem o botão
  "Desvincular Grupos" em si, porque o ciclo só tem 1 processo cadastrado; a descrição desses dois
  fluxos continua baseada no código (comportamento simétrico ao que foi confirmado no fluxo de
  1 processo).

**Validação pós-edição:** âncoras (0 ausentes), imagens (49 referências, todas existentes),
travessões (1, placeholder já conhecido) - todos OK.


## Complemento à Rodada 15: seção de Redefinir Senha por Admin documentada

Adicionada a subseção "Redefinir a senha de outro usuário" na seção 2 do Capítulo do Admin,
cobrindo a subseção colapsável "Alterar Senha" do modal Editar/Aprovar Usuário (campos Nova Senha
e Confirmação). Prints: img_52_admin_alterar_senha_expandido.png,
img_53_admin_alterar_senha_preenchido.png. Também acrescentada uma nota na seção 3 (Como Fazer
Login) sobre o link "Esqueceu a sua senha?", que só mostra um aviso (sem envio de e-mail) apontando
para essa mesma funcionalidade do Admin.

Validação pós-edição: âncoras (0 ausentes), imagens (51 referências, todas existentes), travessões
(1, placeholder já conhecido) - OK.


## Rodada 16: Novo Capítulo Dedicado de Serventia/Cartório (SC)

Criado o capítulo próprio "Capítulo de Serventia/Cartório (SC)", posicionado entre o Capítulo do
Aluno e Notificações do Sistema, cobrindo o que é exclusivo desse papel (a navegação geral já é a
do Capítulo do Aluno):

1. Visão geral: Área do Aluno mostra TODOS os processos do ciclo ("Processos da Vara"), não só
   os do próprio grupo.
2. Vincular Grupo a Processo: aponta para a seção 12 do Capítulo do Aluno (já escrita e validada
   na Rodada 15), sem duplicar.
3. Modificar Dados do Processo e Alterar Parte: **novo**, testado ao vivo como Rafael. Confirmei
   que "Modificar Dados" (desabilitado para Aluno comum) fica habilitado para SC, com todos os
   campos do processo editáveis. "Alterar Parte" também testado, com o aviso do próprio sistema
   de que a alteração vale para todos os processos em que a parte figura.
4. Movimentar Processo como SC: expliquei o mecanismo (já documentado na seção 9 do Aluno) e listei
   os tipos de movimentação autorizados para SC, com base na migração
   movimentacoes/migrations/0004_popular_catalogo_movimentacao.py (catálogo fechado de 83+3 tipos
   de movimentação, com papéis autorizados, pré-condições e efeitos de status/prazo/notificação —
   fonte de verdade valiosa para os próximos capítulos de APA/APP/MP/JZ também).
   - **Testado ao vivo**: registrei a movimentação "Custas Recolhidas" no processo já Autuado
     (Passo 1 → Passo 2 revisão → Confirmar), sucesso confirmado, evento apareceu na aba Eventos
     do Processo.
   - Os demais tipos exclusivos do SC (citação em suas variantes, revelia, publicação/intimação,
     trânsito em julgado, arquivamento etc.) **não foram testados um a um** - documentados como
     "baseado no código", com aviso explícito no manual.
   - Descoberta lateral: o filtro por tipo de evento e a caixa "Bloquear/Desbloquear" na aba
     Eventos do Processo são elementos **puramente decorativos** (disabled no HTML,
     processos/templates/processos/visualizar_processo.html), sem nenhuma função real - anotado
     no manual para não confundir quem for usar o simulador.

4 prints novos: img_54_sc_modificar_dados_modal.png, img_55_sc_alterar_parte_modal.png,
img_56_sc_movimentar_tipos_dropdown.png, img_57_sc_evento_custas_recolhidas.png.

Validação pós-edição: âncoras (0 ausentes), imagens (55 referências, todas existentes), travessões
(1, placeholder já conhecido) - OK.

## Rodada 17 — Capítulos de Advogados Polo Ativo (APA) e Polo Passivo (APP)

1. Capítulo APA (Advogados Polo Ativo): seção única "Restrições e Movimentações Disponíveis".
   - Testado ao vivo como Mariana (aluna vinculada a grupo com cargo APA num processo autuado):
     confirmei que "Modificar Dados" e "Alterar Parte" aparecem desabilitados no menu do processo -
     essas duas ações continuam exclusivas do papel SC, como já documentado no capítulo SC.
   - Testado ao vivo: abri o formulário de Movimentar Processo como Mariana e só "Juntada de
     Documentos" apareceu disponível no processo no estágio atual (pré-condições dos demais tipos
     ainda não satisfeitas nesse processo de teste).
   - Lista completa dos tipos de movimentação autorizados para APA foi extraída do catálogo
     movimentacoes/migrations/0004_popular_catalogo_movimentacao.py (mesma fonte usada no capítulo
     SC), com aviso explícito de que a maior parte não foi testada ao vivo um a um - só o mecanismo
     de filtragem por pré-condição, que já é o mesmo mecanismo genérico documentado na seção 9 do
     capítulo do Aluno.
   2 prints novos: img_58_apa_opcoes_menu_restrito.png, img_59_apa_movimentar_juntada.png.

2. Capítulo APP (Advogados Polo Passivo): seção única de movimentações.
   - Não repeti o teste ao vivo de Modificar Dados/Alterar Parte para APP porque a lógica de
     permissão (processos/permissions.py::pode_editar_processo) é idêntica para APA e APP - só
     Admin/Coordenador/Professor/SC podem editar, então o resultado já está coberto pelo teste do
     APA. Anotei isso explicitamente no manual para não passar a impressão de teste duplicado sem
     necessidade.
   - Lista completa dos tipos de movimentação autorizados para APP, também derivada do catálogo,
     com o mesmo aviso de "não testado ao vivo" onde aplicável. Nenhum print novo específico do APP
     (reaproveitei os prints conceituais do APA, já que a tela é idêntica).

3. Ajuste de padronização: os dois novos títulos de capítulo e as entradas correspondentes no
   Índice usavam travessão ("Advogados — Polo Ativo (APA)"), inconsistente com o resto do
   documento (glossário e corpo do texto usam "Advogados Polo Ativo"/"Advogados Polo Passivo",
   sem travessão). Corrigido para manter o padrão único do manual. Também corrigidos mais 4
   travessões que haviam entrado no texto novo (trocados por dois-pontos ou ponto-e-vírgula,
   mesmo padrão já usado nas rodadas anteriores).

Validação pós-edição: âncoras (0 ausentes), imagens (0 ausentes), travessões (1, placeholder já
conhecido) - OK.

## Rodada 18: Criação de dados de teste para MP e JZ + Capítulos do Ministério Público e do Juiz

**Contexto:** o ciclo NPJ Cível 2026/2 não tinha nenhum grupo com papel Ministério Público (MP) ou
Juiz (JZ) até agora, então esses dois papéis não podiam ser testados ao vivo. Criei os dados de
teste necessários antes de escrever os capítulos.

**1. Dados de teste criados (login como Camila, Professor/Coordenador):**
- Novo grupo "Promotoria de Justiça de Formosa" (papel Ministério Público) no ciclo NPJ Cível
  2026/2, via "Gerenciar Grupos" (mesmo fluxo já documentado na seção 4 do Capítulo do Admin).
- Novo grupo "1ª Vara Cível de Formosa" (papel Juiz), no mesmo ciclo.
- Dois novos alunos cadastrados e aprovados: Fernando Ribeiro Castro (fernando.castro@exemplo.com)
  e Patricia Almeida Rocha (patricia.rocha@exemplo.com), senha padrao "Simu@Teste2026", cada um
  adicionado a um dos dois grupos novos.
- Login como Rafael (SC) para vincular os dois grupos novos ao processo de teste já usado nos
  demais capitulos (0000001-74.2026.8.26.0001), via "Atribuir Grupo ao Processo" (mesmo fluxo já
  documentado na secao 12 do Capitulo do Aluno / secao 2 do Capitulo SC). O processo agora tem 5
  grupos vinculados: SC, APA, APP, MP e JZ.

**2. Capítulo do Ministério Público (MP):**
- Testado ao vivo (login como Fernando, grupo Promotoria de Justiça de Formosa): "Modificar Dados"
  desabilitado no menu "Opções Processo", igual aos demais papéis não-SC. No formulário
  "Movimentar", só "Juntada de Documentos" disponível no estágio atual do processo (mesmo
  transversal já visto para APA e APP).
- Lista completa de movimentações do MP extraída do catálogo (mesma fonte das rodadas anteriores),
  incluindo a acao exclusiva "Manifestação do MP" e uma nota explicando que ela só aparece depois
  que o Juiz decide, na movimentação "MP Deve Intervir: Sim", que a intervenção é obrigatória.
- 1 print novo: img_60_mp_movimentar_juntada.png.

**3. Capítulo do Juiz (JZ):**
- Testado ao vivo (login como Patricia, grupo 1ª Vara Cível de Formosa): mesma restrição de
  "Modificar Dados" desabilitado. No formulário "Movimentar", só "Desentranhamento" disponível
  (o transversal exclusivo do Juiz).
- Lista de movimentações do Juiz extraída do catálogo e organizada por fase do processo (análise
  da inicial, tutela de urgência, citação, audiência de conciliação, revelia, intervenção do MP,
  instrução, sentença, fase recursal), já que é de longe o papel com mais movimentações possíveis
  no sistema - praticamente toda a condução do processo é dele.
- 1 print novo: img_61_jz_movimentar_desentranhamento.png.
- 1 print adicional (usado como referência visual geral, mostrando os 5 grupos ja vinculados ao
  processo de teste): img_62_processo_todos_grupos_vinculados.png.

**Observação sobre nomes de movimentação com travessão no código:** varios nomes de movimentação no
catálogo usam travessão como separador literal (ex.: "Análise da Inicial — Irregular",
"Audiência de Conciliação — Com Acordo", "MP Deve Intervir — Sim"). Para manter a regra do manual
de nao usar travessões na prosa, essas listas foram reescritas de forma descritiva (ex.: "efeitos
da revelia, produz ou não efeito"), em vez de citar o nome literal do sistema - mesmo padrão ja
usado no Capítulo SC para as Modalidades de Citação.

Validação pós-edição: âncoras (0 ausentes), imagens (0 ausentes), travessões (1, placeholder já
conhecido) - OK.

## Rodada 19: "Guia Geral do Simulador" (último capítulo do roteiro)

**Contexto:** último item do roteiro aprovado pelo usuário ("Ordem da home do sistema": SC → APA
→ APP → MP → JZ → Guia geral). Corresponde ao card "Guia geral do simulador" (GERAL) da tela de
login, que descreve "Primeiro acesso, navegação, ciclos e prazos".

**Conteúdo novo, inserido entre "Introdução" e "Primeiros Passos":**
1. **O que é comum a todos os perfis**: elementos fixos do cabeçalho (notificações, Minha Conta,
   A+/A-, contador de sessão) e o seletor de ciclo ativo, exclusivo do Aluno - reunindo referências
   a coisas já documentadas em capítulos anteriores, sem duplicar o conteúdo.
2. **Ciclos, Grupos e Papéis**: tabela-resumo dos 5 papéis processuais (SC, APA, APP, MP, JZ), com
   um resumo de uma linha de cada um e link para o capítulo correspondente - o primeiro "mapa"
   consolidado desses 5 capítulos no manual.
3. **O que são "prazos" no sistema**: conteúdo novo, nunca antes explicado no manual. Baseado na
   estrutura dos efeitos colaterais no catálogo (movimentacoes/migrations/0004_popular_catalogo_movimentacao.py):
   abre_prazo, encerra_prazo, reabre_prazo, notifica, agenda_audiencia. Explicado em nível
   conceitual (o que cada efeito faz), sem repetir prazo a prazo de cada uma das 80+ movimentações.
4. **Avisos operacionais**: os 4 itens do painel "Informações Importantes" da tela de login,
   expandidos e lidos ao vivo (login incluído): liberação pelo coordenador (já documentado),
   limite de 7 MB por arquivo com validação de conteúdo (não só extensão - já mencionado, agora
   citado aqui também), timeout de sessão de 15 minutos com aviso prévio (conteúdo novo) e
   segredo de justiça (conteúdo novo, baseado só na descrição do próprio sistema - não testei ao
   vivo essa restrição, pois nenhum processo de teste usado no manual está marcado como segredo de
   justiça).

Nenhum print novo nesta rodada (seção só reorganiza/explica, sem telas exclusivas a documentar).

Com isso, o roteiro completo aprovado pelo usuário (SC, APA, APP, MP, JZ, Guia Geral) está
concluído.

Validação pós-edição: âncoras (0 ausentes), imagens (0 ausentes), travessões (1, placeholder já
conhecido) - OK.

## Rodada 20: Verificação e correção da marcação residual em "Devolver para Revisão"

**Contexto:** ao revisar o manual em busca de marcações "em elaboração" ainda pendentes, encontrei
uma na seção "Como Avaliar uma Movimentação" (Professor), sobre o botão "Devolver para Revisão".
Diferente do caso do Menu Audiências e "Marcar Audiência" (que checei no código - agendamentos/
views.py e models.py estão vazios, então a funcionalidade realmente não existe ainda), o botão
"Devolver para Revisão" **está implementado** (avaliacoes/views.py, ação "devolver": grava o
FeedbackProfessor com nota=None e mensagem "Movimentação devolvida para revisão."). Era só a
descrição no manual que estava incompleta.

**Teste ao vivo (login como Camila, Professor):**
1. Abri "Avaliações Pendentes" (14 pendentes na conta), escolhi a movimentação "Juntada de
   Documentos" de Lucas Andrade Monteiro (uma das já usadas nos dados de teste).
2. Preenchi um comentário sem marcar nenhuma estrela e cliquei "Devolver para Revisão".
3. Confirmado: a movimentação some da lista de "Avaliações Pendentes" (contador caiu de 15 para
   14) - ou seja, "devolver" conta como uma resposta do Professor, não deixa a movimentação em
   aberto para nova rodada de avaliação.
4. Login como Lucas (Aluno): em "Minhas Notas", a nova linha aparece na aba "Sem Nota", com "—" no
   lugar das estrelas na coluna Avaliação. Abrindo o ícone de "olho", o modal "Detalhe da
   Avaliação" mostra "sem nota" no lugar das estrelas e o comentário do Professor normalmente.
   Indicador "Avaliadas: 1 de 2 movimentações" confirma que só a avaliação com nota conta nesse
   contador; a Média Geral também só considera avaliações com nota.

**Atualização no manual:** removida a marcação "em elaboração"; parágrafo novo descrevendo o
comportamento confirmado, com aviso explícito de que "Devolver para Revisão" **não reabre a
movimentação para o aluno editar** - é só um feedback sem nota. 1 print novo:
img_63_aluno_avaliacao_sem_nota_detalhe.png.

**Tarefas antigas do roteiro (#2-#11) revisadas:** ao conferir o índice do manual contra a lista de
tarefas desta sessão, confirmei que todas as tarefas #2 a #11 (cadastro/aprovação de Lucas, criação
do grupo Monteiro & Advogados Associados, vínculo do grupo ao processo, anexo de arquivo,
editor on-line, avaliação de movimentação, Minhas Notas, notificações, bloqueio de cadastro,
capítulo de ciclos/grupos) já estavam refletidas no manual (criadas em rodadas anteriores a esta
sessão) - eram apenas itens da lista de tarefas que não tinham sido marcados como concluídos.
Marcadas como concluídas nesta rodada, sem necessidade de retrabalho.

Validação pós-edição: âncoras (0 ausentes), imagens (0 ausentes), travessões (2, ambos
placeholders legítimos do próprio sistema - "—"/"0" em Minhas Notas vazio e "—" na avaliação sem
nota) - OK.
