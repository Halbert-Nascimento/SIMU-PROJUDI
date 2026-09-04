# 🎓 Simulador Universitário Projudi

Projeto acadêmico de simulação do sistema Projudi desenvolvido por alunos da Faculdade IESGO.

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

### 5. Execute as migrações do banco de dados

```bash
python manage.py migrate
```

### 6. Rode o servidor de desenvolvimento

```bash
python manage.py runserver
```

### 7. Acesse o sistema

Abra seu navegador e acesse:

```
http://127.0.0.1:8000/
```

## 📦 Estrutura do Projeto

```
simu-projudi/
├── core/               # Configurações principais do Django
├── acesso/             # App de autenticação e página inicial
├── processos/          # App de gerenciamento de processos
├── usuarios/           # App de gerenciamento de usuários
├── templates/          # Templates base compartilhados
├── docs-tuto/          # Documentação e tutoriais
├── pyproject.toml      # Configuração do projeto e dependências
├── manage.py           # Script de gerenciamento do Django
└── README.md           # Este arquivo
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- **Django 6.0** - Framework web
- **uv** - Gerenciador de pacotes
- **SQLite** - Banco de dados (desenvolvimento)
- **Tailwind CSS** - Framework CSS
- **Font Awesome** - Ícones

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

### Listar pacotes instalados

```bash
uv pip list
```

### Instalar novo pacote

```bash
uv pip install nome-do-pacote
```

## ✅ Testes

O projeto não tem suíte automatizada de back-end (os `tests.py` estão vazios).
O que existe hoje é um teste de comportamento do paginador:

```bash
node scripts/teste_paginador.mjs
```

Ele roda `static/js/paginador.js` contra um DOM mínimo (39 asserções) e cobre,
entre outras coisas, a **reserva de espaço**: um bloco paginado não pode encolher
quando a última página tem menos linhas, e numa tabela a linha solitária não pode
ficar centralizada num bloco alto. Esse defeito já apareceu três vezes, por
caminhos diferentes — **ao criar uma listagem paginada nova, acrescente o caso
aqui e confira a última página no navegador antes de considerar pronto.**

## 🎨 Identidade Visual

O projeto segue a identidade visual do sistema Projudi do TJGO, utilizando:

- Azul marinho (#153a61) - Header e elementos principais
- Azul (#1a5b9e) - Botões e links
- Cinza claro (#e9e9e9) - Cards e backgrounds

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais.

## 🚧 Status do Projeto

**Em Desenvolvimento** - Projeto em fase de construção como simulador universitário.

---

**Faculdade IESGO** | Simulador Universitário Projudi
