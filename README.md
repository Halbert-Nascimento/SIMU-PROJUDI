# 🎓 Simulador Universitário Projudi

Projeto acadêmico de simulação do sistema Projudi desenvolvido por alunos da Faculdade IESGO.

> **Licença:** [PolyForm Strict 1.0.0](LICENSE) — © 2026 Halbert Nascimento, Cauê Gomes Machado e Eduardo Netto Freyer.
> O código pode ser lido, estudado e executado para fins não comerciais, mas **não pode ser copiado, modificado nem distribuído**.
> Resumo em português: [LICENSE.pt-BR.md](LICENSE.pt-BR.md).

## 👥 Autores

- [Cauê Gomes Machado](https://github.com/CaueMachado07)
- [Eduardo Netto Freyer](https://github.com/EduardoFreyer)
- [Halbert Nascimento](https://github.com/Halbert-Nascimento)

## 📋 Pré-requisitos

- Python 3.11 ou superior
- [uv](https://github.com/astral-sh/uv) - Gerenciador de pacotes Python rápido

### Instalando o uv

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **⚠️ IMPORTANTE:** Após a instalação, **feche e abra novamente o terminal** (ou PowerShell) para que o `uv` seja reconhecido no PATH.

**Se o comando `uv` não for reconhecido:**

1. **Windows**: Adicione manualmente ao PATH do sistema:
   - Caminho padrão: `%USERPROFILE%\.cargo\bin`
   - Ou: `C:\Users\SeuUsuario\.cargo\bin`
2. **Reinicie o terminal/PowerShell** após adicionar ao PATH

3. Verifique se funcionou:
   ```bash
   uv --version
   ```

## 🚀 Como executar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/Lads-iesgo/SIMU-PROJUDI.git
cd simu-projudi
```

### 2. Crie o ambiente virtual

```bash
uv venv
```

### 3. Ative o ambiente virtual

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 4. Instale as dependências

```bash
# Instalar apenas as dependências principais
uv pip install -e .

# OU instalar com dependências de desenvolvimento
uv pip install -e ".[dev]"
```

### 5. Configure o arquivo `.env`

Crie um `.env` na raiz do projeto (ele é ignorado pelo Git). `SECRET_KEY` e
`DATABASE_URL` são obrigatórios; o restante tem valor padrão.

```env
SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
DEBUG=True
DATABASE_URL=mysql://usuario:senha@127.0.0.1:3306/projudi
ALLOWED_HOSTS=127.0.0.1,localhost

# Em desenvolvimento local, sem HTTPS:
SECURE_SSL_REDIRECT=False
```

O sistema exige **MySQL** (driver `mysqlclient`): as migrações usam SQL
específico do MySQL, então o SQLite não é suportado, nem para testes.

Outras variáveis aceitas: `CSRF_TRUSTED_ORIGINS`, `SESSION_TIMEOUT_SECONDS`
(padrão 900), `BEHIND_TLS_PROXY`, `SECURE_HSTS_SECONDS`,
`SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `NOME_INSTITUICAO`,
`FORO_COMARCA` e `EMAIL_CONTATO_DPO`.

### 6. Execute as migrações do banco de dados

```bash
python manage.py migrate
```

### 7. Rode o servidor de desenvolvimento

```bash
python manage.py runserver
```

### 8. Acesse o sistema

Abra seu navegador e acesse:

```
http://127.0.0.1:8000/
```

## 📦 Estrutura do Projeto

```
simu-projudi/
├── core/               # Configurações do Django (settings, urls, wsgi/asgi)
├── base/               # Infraestrutura compartilhada: componentes e layouts de
│                       #   template, templatetags (card, modal, campo), classes de
│                       #   botão/campo (ui.py), mensagens, decorators, storage
├── usuarios/           # Modelo de usuário e perfis (Admin, Coordenador,
│                       #   Professor, Aluno, Pendente)
├── acesso/             # Login, cadastro, termos, gestão de usuários, middlewares
│                       #   de sessão
├── ciclos/             # Ciclos de simulação, grupos de trabalho e cargos
├── processos/          # Processos judiciais, partes e documentos
├── movimentacoes/      # Movimentações processuais e catálogo de tipos
├── avaliacoes/         # Notas, estrelas e relatórios de avaliação
├── notificacoes/       # Notificações do usuário
├── agendamentos/       # Agendamentos (app ainda sem funcionalidades)
├── manual/             # Manual do usuário publicado dentro do sistema
├── manual-usuario/     # Fonte do manual (Markdown), roteiro e dados de teste
├── templates/          # Páginas de erro (400/403/404/500) e arquivos estáticos
│   └── static/         #   css/, js/, img/, favicon_io/ e modelos/
├── scripts/            # Seeds, verificadores de interface e testes de JavaScript
├── pyproject.toml      # Configuração do projeto e dependências
├── manage.py           # Script de gerenciamento do Django
└── README.md           # Este arquivo
```

Cada app de domínio segue o mesmo desenho: `models.py`, `views.py`, `urls.py`,
`forms.py`, `permissions.py` (funções puras de autorização) e, quando preciso,
`services.py` e `templatetags/<app>_ui.py`. Os testes ficam em `tests.py` ou na
pasta `tests/` de cada app.

Pastas criadas em tempo de execução e ignoradas pelo Git: `.venv/`,
`arquivos_privados/` (documentos processuais) e `staticfiles/`.

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- **Django 6.0** - Framework web (renderização no servidor, sem API REST)
- **uv** - Gerenciador de pacotes
- **MySQL** (`mysqlclient`) - Banco de dados; `DATABASE_URL` via `django-environ`
- **django-private-storage** - Armazenamento protegido dos documentos processuais
- **python-magic** - Validação do tipo real dos arquivos enviados
- **Tailwind CSS** - Framework CSS (tokens em `templates/static/js/tailwind.config.global.js`)
- **Font Awesome** - Ícones
- **pytest / pytest-django, ruff, black** - Testes e qualidade de código (extra `dev`)

## 📝 Comandos Úteis

### Criar um novo app Django

```bash
python manage.py startapp nome_do_app
```

### Criar migrações

```bash
python manage.py makemigrations
```

### Aplicar migrações

```bash
python manage.py migrate
```

### Criar superusuário

```bash
python manage.py createsuperuser
```

### Verificar a configuração do projeto

```bash
python manage.py check
```

### Popular o banco com dados de exemplo

Seed idempotente (`get_or_create`): pode ser rodado mais de uma vez.

```bash
python manage.py shell -c "exec(open('scripts/seed_pos_migracao.py', encoding='utf-8').read())"
```

> `scripts/seed_pre_migracao.py` é o equivalente para o schema anterior à
> separação do app `movimentacoes`; só serve para validar aquela migração.

### Gerar o manual do usuário

O manual é escrito em Markdown (`manual-usuario/MANUAL_DO_USUARIO.md`) e
convertido em páginas HTML por capítulo, publicadas no app `manual`:

```bash
python scripts/gerar_manual_html.py           # gera as páginas
python scripts/gerar_manual_html.py --check   # falha se o gerado estiver desatualizado
```

Requer `markdown-it-py` (extra `dev`); o servidor não precisa dele, porque o
resultado é versionado em `manual/` (capítulos, `metadados.json` e o índice de
busca `manual/static/manual/busca.json`). Rode o comando sempre que alterar o
Markdown ou as imagens em `manual-usuario/assets/` e **versione os arquivos
gerados**.

### Coletar arquivos estáticos (produção)

```bash
python manage.py collectstatic --noinput
```

### Listar pacotes instalados

```bash
uv pip list
```

### Instalar novo pacote

```bash
uv pip install nome-do-pacote
```

## ✅ Testes

### Back-end (Django)

A suíte de back-end tem cerca de 230 testes, distribuídos em `acesso`, `base`,
`ciclos`, `usuarios`, `notificacoes`, `manual` e nas pastas `tests/` de
`avaliacoes`, `movimentacoes` e `processos`. O app `agendamentos` ainda não tem
testes. Instale o extra `dev` (`uv pip install -e ".[dev]"`) e rode:

```bash
pytest                                  # tudo (configurado no pyproject.toml)
pytest movimentacoes                    # um app
python manage.py test processos         # alternativa pelo runner do Django
```

Os testes criam um banco de teste próprio; com MySQL, o usuário do `DATABASE_URL`
precisa de permissão para criar bancos.

### Front-end (JavaScript)

Os testes de JavaScript exigem [Node.js](https://nodejs.org/) e não usam jsdom
nem runner: cada script traz um DOM mínimo escrito à mão. O primeiro cobre o
paginador:

```bash
node scripts/teste_paginador.mjs
```

Ele roda `templates/static/js/paginador.js` contra esse DOM e cobre,
entre outras coisas, a **reserva de espaço**: um bloco paginado não pode encolher
quando a última página tem menos linhas, e numa tabela a linha solitária não pode
ficar centralizada num bloco alto. Esse defeito já apareceu três vezes, por
caminhos diferentes — **ao criar uma listagem paginada nova, acrescente o caso
aqui e confira a última página no navegador antes de considerar pronto.**

```bash
node scripts/teste_mascara_moeda.mjs
```

Cobre a máscara monetária de `templates/static/js/mascara_moeda.js`, usada
pelo cadastro de processo e pelo modal "Modificar Dados": o dígito entra pelos
centavos e empurra o valor para a esquerda — digitar `1` dá R$ 0,01 e `2000` em
seguida dá R$ 120,00.

> Verde não é prova: antes de confiar numa asserção nova, reintroduza o defeito
> e confira que o teste fica **vermelho**. Já aconteceu de o simulador de DOM
> confirmar a suposição errada do código que ele deveria testar.

### Verificação da interface

Dois scripts guardam a troca de pele pelo Guia de Design:

```bash
python scripts/verificar.py snapshot   # antes de mexer numa tela
python scripts/verificar.py check      # compilação, aninhamento, classes órfãs,
                                       # escala tipográfica, raio/sombra em CSS
python scripts/verificar.py diff       # o que mudou de texto visível e de id
python scripts/render_smoke.py         # renderiza as telas do lote, com e sem dados
```

O invariante de uma troca de pele: **o texto visível e o conjunto de `id` não
mudam — só atributos.** `snapshot` grava o estado antes, `diff` acusa o que
sumiu. `check` não renderiza; `render_smoke.py` é quem executa `{% card %}`,
`{% campo %}` e os `{% include %}` de componente, onde os erros de argumento
aparecem.

## 🎨 Identidade Visual

O projeto segue o **Guia de Design da Faculdade IESGO** (versão 1.0),
`Guia de Design SIMU-PROJUDI.dc.html`, mantido fora deste repositório. As
regras de uso (tokens, tipografia, componentes):

- Navy IESGO (#0a083d) — cabeçalho, títulos e botão primário
- Azul de ação (#1f4f9c) — links, aba ativa e foco de campo
- Vermelho institucional (#d30000) — só fio de assinatura, nunca botão ou link
- Barlow (interface) + Lato (dado codificado), base 12px
- Cantos retos, sem sombra fora de modal; hierarquia por borda de 1px e faixa de 3px

## 📄 Licença

Projeto acadêmico (TCC) desenvolvido para fins educacionais, licenciado sob a
[PolyForm Strict License 1.0.0](LICENSE): código visível e de uso não comercial,
sem direito de distribuir nem de modificar. Resumo em português em
[LICENSE.pt-BR.md](LICENSE.pt-BR.md).

## 🚧 Status do Projeto

**Em Desenvolvimento** - Projeto em fase de construção como simulador universitário.

---

Simulador Universitário Projudi
