# Instruções do Projeto — simu-projudi

## Visão Geral

Simulador universitário do sistema Projudi (TJGO). Stack: **Django 6 + MySQL + Tailwind CSS**.
Projeto server-side rendered (sem API REST) — views Django + templates HTML.

---

## Boas Práticas Obrigatórias

### Antes de Implementar Qualquer Coisa

1. **Leia as views, models e templates existentes** da feature ou área que será alterada.
2. **Verifique o `permissions.py` do app envolvido** antes de adicionar qualquer lógica de acesso.
3. **Confirme que a interface atual não será quebrada** — identifique quais templates, URLs e formulários existentes são afetados.
4. **Se houver dúvida ou conflito**, informe o problema e proponha alternativas antes de implementar.

---

## Sistema de Permissões

O projeto usa **funções puras** em `permissions.py` por app — não decoradores Django genéricos.
Sempre consultar e reutilizar as funções existentes antes de criar novas.

| App | Arquivo | Funções principais |
|---|---|---|
| `acesso` | `acesso/permissions.py` | `pode_gerenciar_usuarios()`, `tipos_que_pode_atribuir()` |
| `ciclos` | `ciclos/permissions.py` | `pode_criar_ciclo()`, `pode_editar_ciclo()`, `pode_gerenciar_grupos_ciclo()`, `pode_ver_todos_ciclos()`, `pode_ver_ciclos_arquivados()` |
| `processos` | `processos/permissions.py` | `pode_visualizar_processo()` (inclui lógica de segredo de justiça), `pode_editar_processo()` |
| `movimentacoes` | `movimentacoes/permissions.py` | `pode_praticar_movimentacao()`, `tipos_praticaveis()`, `grupo_processo_do_usuario()` |
| `avaliacoes` | `avaliacoes/permissions.py` | `pode_ver_minhas_notas()`, `perfil_pode_avaliar()`, `pode_avaliar_movimentacao()` |

**Hierarquia de perfis:** Admin > Coordenador > Professor > Aluno > Pendente

Ao adicionar nova permissão: adicione no `permissions.py` do app correto como função pura, nomeie com o padrão `pode_<acao>_<recurso>()`.

---

## Banco de Dados — ORM Obrigatório

- **Nunca use SQL puro** (`cursor.execute`, `raw()`) sem justificativa documentada.
- Use sempre o ORM do Django: `QuerySet`, `select_related`, `prefetch_related`, `annotate`, `aggregate`.
- Casos onde SQL direto pode ser aceito: operações de migração de dados complexas ou queries com performance crítica comprovada — sempre justificado com comentário.

### Evitar N+1

Padrões que geram N+1 (proibidos sem correção):

```python
# ERRADO — N+1
for processo in ProcessoJudicial.objects.all():
    print(processo.ciclo.nome)  # query por iteração

# CORRETO
for processo in ProcessoJudicial.objects.select_related("ciclo").all():
    print(processo.ciclo.nome)
```

Regras práticas:
- FK simples → `select_related("campo")`
- M2M ou FK reversa → `prefetch_related("campo")`
- Contagens em lista → `annotate(total=Count(...))`
- Nunca acesse relacionamentos dentro de um loop sem ter feito o prefetch antes.

---

## Segurança

### Upload de Arquivos
- Limite: **7 MB** (`MAX_FILE_SIZE_MB`)
- Extensões permitidas: `.pdf`, `.docx`, `.jpg`, `.jpeg`
- MIME types validados por `python-magic` (não confiar apenas na extensão)
- Documentos processuais ficam em `arquivos_privados/` via `django-private-storage`

### Segredo de Justiça
- Sempre verificar `pode_visualizar_processo()` antes de expor dados de processo
- Processos com `segredo_justica=True` têm regras de acesso diferenciadas — nunca ignorar esse campo

### Validação de Formulários
- Toda entrada do usuário passa por `Form` ou `ModelForm` do Django
- Nunca confiar em dados de `request.POST` sem passar pelo form
- Campos de arquivo sempre validados com `python-magic` além do form

### Sessão
- Timeout configurável via `.env` (`SESSION_TIMEOUT_SECONDS`, padrão 900s)
- `SessionActivityMiddleware` e `CicloAtivoMiddleware` são ativos — não interferir sem entender o impacto

---

## Arquitetura e Organização

### Estrutura padrão de app
```
<app>/
├── models.py          # entidades de dados
├── views.py           # ou views_<area>.py para apps grandes
├── urls.py            # roteamento
├── forms.py           # ou forms_<area>.py
├── permissions.py     # funções puras de autorização
├── admin.py           # configuração do admin
├── services.py        # lógica de negócio não trivial (quando necessário)
├── utils.py           # utilitários auxiliares
├── middleware.py      # middlewares específicos do app
└── templates/<app>/   # templates do app
```

### Regras de organização
- Lógica de negócio complexa vai em `services.py`, não em views
- Views devem ser enxutas: validar form → chamar service/model → retornar resposta
- Nunca duplicar lógica de permissão já existente em `permissions.py`
- Ao crescer muito, dividir views em `views_<area>.py` (ex: `views_movimentacao.py`)

---

## Design — Guia IESGO

A identidade do sistema é a da **Faculdade IESGO**, definida no
`design/Guia de Design SIMU-PROJUDI.dc.html` (versão 1.0, fora do repositório).
O acompanhamento da conversão está em `../NOVO-DESIGN.md`.

> **A identidade do Projudi/TJGO foi aposentada.** Os azuis `#153a61` e `#1a5b9e`,
> cantos arredondados, sombras em card e gradientes estão na lista de *Não faça*
> do guia. Se aparecer um deles, é resquício — não é referência.

**A regra de ouro do guia: copie daqui, não crie variação.** Precisou de uma cor,
um tamanho ou um estado que não existe? A pergunta certa não é "qual hex inventar",
é "essa distinção precisa mesmo estar na cor?".

### Onde mora cada decisão

Quase toda a pele está concentrada em poucos arquivos. Mexer neles repinta o
sistema inteiro; mexer num template repinta uma tela.

| Arquivo | O que governa |
|---|---|
| `templates/static/js/tailwind.config.global.js` | tokens de cor, escala tipográfica, raio, sombra, z-index, largura |
| `base/ui.py` | cadeias de classe de botão (`CLASSES_BOTAO`) e de campo (`CLASSE_CAMPO`) |
| `templates/static/css/componentes.css` | classes de componente compartilhadas (`.pill .modal .tbl-* .tabs .card-kpi .toast`) |
| `templates/static/css/base.css` | estrutura de página, cabeçalho, rodapé |
| `templates/static/css/processos_compartilhado.css` | peças das telas processuais (`.panel .field-* .mov-text .btn-blue .btn-secondary`) |
| `templates/static/css/formularios.css` | fieldset, foco, erro de validação |
| `ciclos/templatetags/ciclos_ui.py`, `processos/templatetags/processos_ui.py` | cor de cada status, decidida em Python |

### Cor — nunca escreva hex num template

Use o token. Há **zero** hexadecimais fora da paleta no projeto, e o verificador
mantém assim.

| Papel | Token | Valor |
|---|---|---|
| Marca, cabeçalho, botão primário, título | `navy` | `#0a083d` |
| Ação — link, aba ativa, foco de campo | `acao` | `#1f4f9c` |
| Assinatura — **só fio**, nunca botão nem link | `marca` | `#d30000` |
| Fundo de página / cabeçalho de card / cabeçalho de tabela | `pagina` / `card-topo` / `tabela-topo` | `#f4f5f7` / `#fbfbfc` / `#f7f8fa` |
| Borda de contêiner / divisor de linha / borda de campo | `contorno` / `divisor` / `campo-borda` | `#e2e5ea` / `#eef0f3` / `#d3d7de` |
| Texto corpo / neutro / rótulo | `texto` / `texto-neutro` / `rotulo` | `#23262e` / `#4b5563` / `#6b7280` |
| Erro de validação de campo | `validacao` | `#c0392b` |

**Estado é sempre um trio fundo/texto/borda, e são exatamente quatro:**

| Trio | Para | Classe pronta |
|---|---|---|
| `ok-bg` `ok-txt` `ok-bd` | em andamento, ativo, sucesso, polo ativo | `.pill ok` |
| `atencao-bg` `atencao-txt` `atencao-bd` | suspenso, prazo, pendência | `.pill warn` |
| `erro-bg` `erro-txt` `erro-bd` | erro, polo passivo | `.pill erro` |
| `neutro-bg` `neutro-txt` `neutro-bd` | arquivado, inativo, encerrado | `.pill gray` |

Não existe um quinto trio. Se a tela tem cinco estados, **dois deles compartilham
cor** — foi o que se fez com as faixas de nota de `minhas_notas`, onde o próprio
número já distingue o que a cor deixou de distinguir.

### Tipografia

**Barlow** na interface, **IBM Plex Mono** em dado codificado. Corpo base **12px**.

| Token | Tamanho | Uso |
|---|---|---|
| `text-micro` | 10px / .1em | rótulo de campo, etiqueta, ação de linha |
| `text-meta` | 10.5px | apoio, erro de validação, botão |
| `text-apoio` | 11px | meta, título de seção e de card |
| `text-dado` | 11.5px | linha de tabela, dado monoespaçado |
| `text-corpo` | 12px | texto corrido |
| `text-h1` | 26px | título de área (um por tela) |
| `text-kpi` | 28px | número de indicador |

- **Nunca** `text-xs`, `text-sm`, `text-xl`, `text-2xl` — resolvem para tamanhos
  reais (12/14/20/24px) que não existem na escala, então pintam sem avisar.
- **Nunca** `text-[13px]` e afins: é a mesma falha escrita de outro jeito.
  Dimensionar **ícone** com valor arbitrário é aceito — a escala é de texto.
- **Nada abaixo de 10px.** Está em *Não faça*.
- **`font-mono` é obrigatória** em número CNJ, CPF/CNPJ, valor da causa, sequência
  de movimentação e códigos. Nunca em texto corrido.

### Densidade, raio e sombra

- **Raio 0** em contêiner e botão. As três exceções: `rounded-campo` (2px, só
  campo de formulário) e `rounded-full` (avatar e ponto de status).
- **Sem sombra fora de modal.** A hierarquia vem de **borda de 1px** e de
  **faixa de 3px**. Também é a faixa de 3px que marca item selecionado.
- Escala de espaçamento entre coisas: **2 / 6 / 8 / 12 / 14 / 18 / 28px**. Os
  paddings internos de componente o guia especifica à parte (linha de tabela
  `11px 16px`, campo `8px 9px`, ação de linha `5px 10px`, etiqueta `3px 9px`) —
  esses não estão na escala e não deveriam estar.
- Sem gradiente. Sem ícone decorativo. Sem emoji.

> `borderRadius` e `boxShadow` são **sobrescritos** no config, não estendidos:
> todo `rounded*` e `shadow*` escrito como classe resolve para 0/none. **Isso não
> alcança CSS escrito à mão** — um `border-radius: 3px` dentro de `<style>` ou de
> um atributo `style=""` passa por fora e continua pintando.

### Estrutura de página

```html
{% nav_secundaria ativo='...' %}
<main class="max-w-conteudo mx-auto px-7 py-5">
```

`max-w-conteudo` são os 1280px do guia e `px-7` os 28px de margem lateral — os
mesmos que o cabeçalho e a navegação usam, então a coluna de conteúdo alinha com
a barra acima dela. Cabeçalho fixo de 60px (z 40), navegação em `top-[60px]`
(z 30), modal z 60, toast z 70.

### Botões

Seis variantes em `CLASSES_BOTAO`, e só elas:

| Variante | Quando |
|---|---|
| `primario` | a **única** ação principal do bloco |
| `secundario` | apoio: limpar, cancelar, voltar, exportar |
| `linha` | ação **dentro de tabela** — menor, para não engordar a linha |
| `destrutivo` | nunca vermelho sólido; a confirmação vem no modal |
| `desabilitado` | sem opacidade global: fundo, texto e cursor próprios |
| `sobre-navy` | sobre a barra escura do cabeçalho |

```html
<button class="{% classe_botao 'primario' padding=True %}">Pesquisar</button>
```

- **Um único primário por bloco.**
- **Primário sempre à esquerda do secundário** (guia, seção 04). Vale inclusive
  em assistente, onde isso põe "Avançar" à esquerda de "Cancelar" — o sistema tem
  uma regra só.
- **Use `padding=True`.** Escrever `py-1.5 px-3 text-[11px]` depois da tag
  sobrescreve o guia com valores que não são dele.
- Dentro de tabela é `linha`, não `primario`.
- As variantes saem com o marcador `btn`, que não pinta nada: ele existe para
  `componentes.css` excluir botão do seletor de link de tabela. Não remova.

### Campos

```html
{% campo label="Nº do processo" erros=form.numero.errors para=form.numero.id_for_label %}
    <input name="numero" class="{% classe_campo mono=True %}">
{% endcampo %}
```

- Rótulo **acima**, caixa alta 10px, gap 5px. `para=` amarra o `<label>`.
- Foco **só por borda** (`#1f4f9c`), sem `ring` e sem outline do navegador.
- `mono=True` em dado codificado.
- Campo obrigatório recebe `*` no rótulo.
- Colunas de formulário usam **frações** (`lg:grid-cols-[1.7fr_1fr]`), nunca
  larguras percentuais mistas.

> **O botão é 3,45px mais baixo que o campo, e os dois números vêm do guia.** O
> padding do campo é fixado textualmente; os ~30px do botão o guia chama de
> "altura resultante". Quem cede é o botão. Com o rótulo fora da linha, resolve
> `items-stretch`; com o rótulo dentro da coluna, declare a altura **em `calc()`
> com os valores do guia**, como em `.filtros .acoes` de `pagina_aluno` — nunca
> um `37.2px` solto, que esconde de onde o número veio.

### Tabelas e listas

- Use `.tbl-projudi` (densidade padrão) ou `.tbl` / `.tbl-hist` / `.tbl-mov`
  (compacta). Sem zebrado: a separação vem do divisor.
- Coluna de ação leva `.col-acoes` — **118px fixos**, nunca `auto`.
- Célula com duas linhas de texto usa `.celula-dupla`.
- Linha: padding 11px 16px, divisor `#eef0f3`, hover `#f7faff`, última sem borda.

> O guia pede grade CSS em vez de `<table>`. **O projeto manteve `<table>`** — o
> resultado visual é idêntico, a semântica serve ao leitor de tela e o paginador
> continua funcionando. É desvio consciente, não descuido. O mesmo vale para os
> ícones do FontAwesome.

### Armadilhas de cascata — as que já custaram caro

1. **Utility vence classe de componente.** `.p-2` solto no HTML vence
   `.accordion-item-closed`. Quando um elemento tem dois estados, **os dois saem
   do mesmo lugar** — duas classes de componente irmãs, nunca uma classe de um
   lado e utilities do outro.
2. **E classe de componente vence utility, quando é mais específica.**
   `.tbl-projudi a` (0-1-1) vence `.text-white` (0-1-0) *sempre* — foi assim que
   o rótulo de um botão primário saiu azul sobre fundo navy. Descendente de
   classe de componente não deve pintar o que um utility pode querer pintar de
   outra cor; se pintar, exclua o caso (`a:not(.btn)`).
3. **Cor decidida no JavaScript é parte da pele.** `classList.add`, `className =`
   e `innerHTML` com classe embutida não aparecem em busca por template. Ao mexer
   numa tela, leia o JS junto — e prefira que o JS alterne **só o nome do estado**
   (`.active`), nunca a cor.
4. **Classe de estilo nunca é seletor de JavaScript.** Um
   `querySelector(".text-texto-secundario")` sobrevive a uma renomeação apontando
   para nada e estoura em `TypeError` sem nada quebrar antes. Gancho de JS é
   classe semântica: `.btn-remover`, `.polo-lista`, `.parte-doc`, `.mov-row`.
5. **Cadeia de `flex-1`/`h-full` sem altura na raiz não faz nada** e não avisa —
   são classes válidas que resolvem para algo, e o layout "quase" funciona.

### Antes de considerar uma tela pronta

```bash
python scripts/verificar.py snapshot   # ANTES de mexer
python scripts/verificar.py check      # compilação, aninhamento, classes órfãs,
                                       # escala de fonte, raio/sombra em CSS
python scripts/verificar.py diff       # texto visível e ids não podem mudar
python scripts/render_smoke.py         # renderiza a tela com e sem dados
```

- **O invariante de uma troca de pele: o texto visível e o conjunto de `id` não
  mudam — só atributos.** Mudança de texto é permitida, mas tem que ser
  deliberada e registrada no `NOVO-DESIGN.md`.
- `check` apenas compila; quem executa `{% card %}`, `{% campo %}` e os
  `{% include %}` de componente é o `render_smoke.py`. Ao converter uma tela,
  acrescente o caso em `CASOS`.
- **Nada disso vê contraste, hover ou menu que abre.** A conferência no navegador
  não é opcional: o botão "Ver Autos" do painel passou por todas as verificações
  sendo ilegível.

---

## Componentes de Interface

Antes de escrever HTML novo, verifique se já existe componente para a peça.

| Componente | Como usar | Onde |
|---|---|---|
| Mensagens do `messages` | `{% include 'base/components/_mensagens.html' %}` (opcional: `with tag="movimentacao"`) | `base` |
| Breadcrumbs | `{% include 'base/components/_breadcrumbs.html' %}` | `base` |
| Listagem vazia | `{% include 'base/components/_estado_vazio.html' with mensagem="..." only %}` | `base` |
| Paginação | `{% include 'base/components/_paginacao.html' with container_id=... only %}` + `criarPaginador()` de `static/js/paginador.js` | `base` |
| Toast | `{% include 'base/components/_toast.html' %}` + `showToast()` de `static/js/toast.js` | `base` |
| Card de indicador (KPI) | `{% include 'base/components/_card_kpi.html' with rotulo="..." numero=... apoio="..." only %}` (`variante="alerta"` para o trio de erro) | `base` |
| Card | `{% card titulo="..." icone="fa-..." %}...{% endcard %}` | `base/templatetags/ui.py` |
| Modal | `{% modal id="..." titulo="..." %}...{% endmodal %}` | `base/templatetags/ui.py` |
| Campo de formulário | `{% campo label="..." erros=form.x.errors %}<input>{% endcampo %}` | `base/templatetags/ui.py` |
| Classes de botão/campo | `{% classe_botao 'primario' %}`, `{% classe_campo %}` | `base/ui.py` |
| Navegação secundária | `{% nav_secundaria %}` | `base/templatetags/ui.py` |
| Status do ciclo | `{% badge_status_ciclo %}`, `{% ponto_status_ciclo %}` | `ciclos/templatetags/ciclos_ui.py` |
| Status do processo | `{% badge_status_processo %}`, `{% pill_status_processo %}` | `processos/templatetags/processos_ui.py` |

### Qual mecanismo usar

```
Depende de dado calculado?
  não → mesmo dado em todo lugar?        → {% include %}
      → dados diferentes a cada uso?      → {% include ... with ... only %}
      → repete só dentro do mesmo arquivo → {% partialdef %}
  sim → envolve conteúdo variável?        → @register.simple_block_tag
      → renderiza a partir de um objeto?  → @register.inclusion_tag
      → devolve texto formatado?          → @register.simple_tag / filter

Precisa de query ao banco? Não é componente de template — vai para services.py ou a view.
```

### Componente com paginação

Sempre que uma listagem for paginada, **verifique que o bloco não muda de altura
ao trocar de página**. A última página quase sempre tem menos linhas; se nada
reservar a altura, o bloco encolhe e a página salta sob o cursor.

- Use `criarPaginador()` de `static/js/paginador.js` — ele reserva o espaço de uma
  página cheia enquanto houver mais de uma página. Não escreva paginação à mão.
- **A reserva é feita de dois jeitos, e o componente escolhe sozinho** pelo pai
  das linhas:
  - listagem em `<table>` → linhas de preenchimento no `<tbody>`. `min-height`
    numa tabela **não sobra embaixo**: ela estica as linhas, e a linha solitária
    da última página fica centralizada num bloco alto.
  - listagem em bloco (`div`) → `min-height` medido no próprio contêiner.
- Se o bloco já tiver altura definida por CSS, a reserva não faz nada — é um
  mínimo, não uma altura fixa.
- `alturaId` troca o elemento onde a reserva mora, quando não for o de `tabelaId`.
- **`aoAtualizar`** roda a cada render, depois de decidir quais linhas aparecem e
  **antes** de medir a reserva. É onde mora a linha que precisa acompanhar outra:
  em `visualizar_processo` cada movimentação tem uma segunda `<tr>` com os
  arquivos dela, que o `rowSelector` não seleciona e que ficaria visível sozinha
  ao trocar de página. Se rodasse depois, a reserva mediria uma altura que o
  callback ainda ia mudar.
- Se a listagem é reconstruída inteira a cada filtro (a tela reescreve o
  `<tbody>` e chama `resetar()`), o paginador remede a página cheia sozinho — não
  é preciso `filtrarRows`.
- Ao adicionar um paginador, acrescente o caso ao teste de paginação antes de
  considerar pronto: é o único teste de comportamento do projeto.

Este defeito já apareceu três vezes por caminhos diferentes — cadeia de altura
decorativa, ausência de altura, e `min-height` esticando linhas de tabela. A
correção mora no componente; o que se pede aqui é **conferir no navegador** a
última página de cada listagem nova.

> **Verde não é prova.** Ao escrever uma asserção nova, reintroduza o defeito e
> confira que ela fica **vermelha** — e que o teste chega até ela, porque um
> `TypeError` no meio esconde tudo o que vem depois. O simulador de DOM já
> confirmou a suposição errada do código três vezes: não medindo nada, dando a
> todas as linhas a mesma altura, e não deixando nenhuma linha ter altura zero.

### Regras de organização

- Prefixo `_` marca template que nunca é renderizado por view — só incluído.
- **`base/components/` não importa model.** Componente que conhece o domínio mora no app dono, em `<app>/templates/<app>/components/`.
- Um arquivo `templatetags/<app>_ui.py` por app, sempre com sufixo `_ui`, para não colidir no `{% load %}`.
- Telas administrativas estendem `base/layouts/layout_admin.html`, não `base/base.html`.
- Classe usada por mais de um template vai para `static/css/componentes.css`; estilo exclusivo de uma tela continua no `<style>` daquela tela.
- **Defeito que reaparece por outro caminho é conserto de componente, não de tela** — e a regra vem para cá, que é onde alguém lê antes de escrever a próxima.

### Helpers de view

- Erros de formulário: `propagar_erros_form(request, form, extra_tags="...")` de `base/mensagens.py`.
- Guarda de permissão que depende só do usuário: `@exige_permissao(pode_x, pode_y)` de `base/decorators.py` (responde 404, como as views já faziam). Permissão que depende de objeto continua explícita na view.
- Tabelas de apoio novas herdam `TabelaDominio` de `base/models.py`.

---

## Comentários no Código

Comentar **apenas o "porquê"**, nunca o "o quê" (o código já diz isso).

```python
# BOM — explica uma regra de negócio não óbvia
# Professor só acessa se for coordenador do ciclo vinculado ao processo
if usuario.tipo_perfil_global == TipoPerfil.PROFESSOR:
    return processo.ciclo.coordenador == usuario

# RUIM — descreve o óbvio
# Verifica se o usuário é professor
if usuario.tipo_perfil_global == TipoPerfil.PROFESSOR:
```

- Comentário máximo: uma linha objetiva
- Sem blocos de comentário multiparágrafo
- Sem comentários que referenciam a tarefa atual ("adicionado para fix X") — esses pertencem ao commit

---

## Nomenclatura Semântica

Evitar nomes genéricos que não identificam o domínio:

```python
# RUIM
def process(obj, data):
def handle(request, id):
queryset = get_items()

# BOM
def registrar_movimentacao(processo, dados_form):
def detalhe_processo(request, processo_id):
processos_do_ciclo = ProcessoJudicial.objects.filter(ciclo=ciclo)
```

Padrões do projeto:
- Views: `lista_<recurso>`, `detalhe_<recurso>`, `criar_<recurso>`, `editar_<recurso>`
- Permissões: `pode_<acao>_<recurso>(usuario, objeto)`
- Services: verbos de domínio — `gerar_numero_cnj()`, `registrar_feedback()`, `encerrar_ciclo()`
- Variáveis de queryset: `<recurso>s_<contexto>` — ex: `processos_do_grupo`, `alunos_pendentes`

---

## Validação Antes de Entregar

Antes de considerar uma implementação concluída:

- [ ] Nenhuma view existente foi quebrada (verificar URLs e templates afetados)
- [ ] Permissões verificadas com as funções do `permissions.py` correto
- [ ] Sem acesso a relacionamentos em loop (N+1)
- [ ] Formulários validam todos os dados de entrada
- [ ] Migrações geradas se modelos foram alterados
- [ ] Nomes de variáveis, funções e views seguem o padrão semântico do projeto
- [ ] Comentários existentes apenas onde o "porquê" não é óbvio
- [ ] Interface segue o guia: token em vez de hex, escala tipográfica, raio 0, `font-mono` em dado codificado
- [ ] `verificar.py check` sem problemas e `diff` sem perda de texto ou de `id`
- [ ] Tela conferida no navegador — hover, menu, modal e última página da listagem

---

## Quando Encontrar Problemas

Se durante a implementação identificar:

- **Conflito de permissões** → parar, descrever o conflito e propor como resolver
- **Risco de quebrar funcionalidade existente** → informar quais views/templates são afetados e propor solução segura
- **Necessidade de SQL puro** → justificar por escrito e propor alternativa ORM primeiro
- **Ambiguidade no requisito** → perguntar antes de implementar, não assumir

Nunca implementar silenciosamente algo que possa quebrar o que já funciona.
