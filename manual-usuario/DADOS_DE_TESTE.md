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
