"""
Seed mínimo para o estado ATUAL do código (Tarefa 0 aplicada: domínio de
movimentação no app `movimentacoes`). Gêmeo de `scripts/seed_pre_migracao.py`
— a única diferença é a origem de `TipoMovimentacao` / `MovimentacaoProcessual`.

Idempotente (get_or_create em tudo). Rodar com:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('scripts/seed_pos_migracao.py', encoding='utf-8').read())"
"""
from decimal import Decimal

from django.contrib.auth import get_user_model

from ciclos.models import (
    CargoSimulacao,
    CicloSimulacao,
    GrupoTrabalho,
    StatusCiclo,
)
from movimentacoes.models import MovimentacaoProcessual, TipoMovimentacao
from processos.models import (
    ClasseProcessual,
    Comarca,
    ParteFicticia,
    PoloProcessual,
    ProcessoJudicial,
    StatusProcessoJudicial,
    TipoProcesso,
    VaraServentia,
)

U = get_user_model()
SENHA = "senha12345"

# --- Lookups de ciclo ----------------------------------------------------------
status_andamento, _ = StatusCiclo.objects.get_or_create(nome_status="Em andamento")
StatusCiclo.objects.get_or_create(nome_status="Arquivado")

CARGOS = [
    ("Serventia/Cartório", "SC"),
    ("Advogados Polo Ativo", "APA"),
    ("Advogados Polo Passivo", "APP"),
    ("Ministério Público", "MP"),
    ("Juiz", "JZ"),
]
cargos = {}
for nome, cod in CARGOS:
    cargos[cod], _ = CargoSimulacao.objects.get_or_create(cod=cod, defaults={"nome": nome})

# --- Lookups de processo -----------------------------------------------------
status_autuado, _ = StatusProcessoJudicial.objects.get_or_create(nome_status="Autuado")
StatusProcessoJudicial.objects.get_or_create(nome_status="Protocolado")
StatusProcessoJudicial.objects.get_or_create(nome_status="Sentenciado")

tipo_proc, _ = TipoProcesso.objects.get_or_create(nome="Conhecimento")
classe, _ = ClasseProcessual.objects.get_or_create(nome="Procedimento Comum Cível")
comarca, _ = Comarca.objects.get_or_create(nome="Comarca de Goiânia")
vara, _ = VaraServentia.objects.get_or_create(nome="1ª Vara Cível", comarca=comarca)

# --- Usuários --------------------------------------------------------------
prof, created = U.objects.get_or_create(
    username="prof.coord",
    defaults={
        "email": "prof.coord@iesgo.edu.br",
        "first_name": "Paula",
        "last_name": "Coordenadora",
        "is_staff": True,
        "is_coordenador": True,
        "tipo_perfil_global": U.TipoPerfilGlobal.PROFESSOR,
    },
)
if created:
    prof.set_password(SENHA)
    prof.save()

alunos = {}
for cod in ("SC", "APA", "APP", "MP", "JZ"):
    u, created = U.objects.get_or_create(
        username=f"aluno.{cod.lower()}",
        defaults={
            "email": f"aluno.{cod.lower()}@iesgo.edu.br",
            "first_name": "Aluno",
            "last_name": cod,
            "tipo_perfil_global": U.TipoPerfilGlobal.ALUNO,
        },
    )
    if created:
        u.set_password(SENHA)
        u.save()
    alunos[cod] = u

# --- Ciclo + grupos -----------------------------------------------------------
ciclo, _ = CicloSimulacao.objects.get_or_create(
    nome_edicao="Simulação de Teste 2026/2",
    defaults={
        "coordenador": prof,
        "semestre": 2,
        "ano": 2026,
        "periodo": 0,
        "status": status_andamento,
    },
)

ciclo.participantes.add(prof, *alunos.values())

grupos = {}
for cod in ("SC", "APA", "APP", "MP", "JZ"):
    g, _ = GrupoTrabalho.objects.get_or_create(
        ciclo=ciclo,
        cargo_simulacao=cargos[cod],
        nome=f"Grupo {cod}",
    )
    g.membros.add(alunos[cod])
    grupos[cod] = g

# --- Partes fictícias --------------------------------------------------------
parte_autor, _ = ParteFicticia.objects.get_or_create(
    cpf_cnpj="111.111.111-11",
    defaults={"nome_razao": "João da Silva", "tipo_pessoa": ParteFicticia.TipoPessoa.FISICA},
)
parte_reu, _ = ParteFicticia.objects.get_or_create(
    cpf_cnpj="22.222.222/0001-22",
    defaults={"nome_razao": "Empresa Ré Ltda.", "tipo_pessoa": ParteFicticia.TipoPessoa.JURIDICA},
)

# --- Processo + movimentação inicial ---------------------------------------
proc = ProcessoJudicial.objects.filter(ciclo=ciclo).first()
if proc is None:
    proc = ProcessoJudicial.objects.create(
        numero=ProcessoJudicial.gerar_numero_cnj(ano=2026, tr=26, origem=comarca.pk),
        ciclo=ciclo,
        vara=vara,
        tipo_processo=tipo_proc,
        classe=classe,
        status_atual=status_autuado,
        valor_causa=Decimal("15000.00"),
        segredo_justica=False,
    )
    proc.grupos.add(grupos["APA"], grupos["SC"])
    PoloProcessual.objects.create(processo=proc, parte=parte_autor, tipo_polo="Ativo")
    PoloProcessual.objects.create(processo=proc, parte=parte_reu, tipo_polo="Passivo")

    tipo_cadastro, _ = TipoMovimentacao.objects.get_or_create(nome_movimentacao="Protocolo da Petição Inicial")
    MovimentacaoProcessual.objects.create(
        descricao_evento=f'Processo "{proc.numero}" cadastrado.',
        processo=proc,
        autor=alunos["APA"],
        tipo_movimento=tipo_cadastro,
    )

print("OK — seed aplicado")
print("  ciclo:      ", ciclo)
print("  grupos:     ", GrupoTrabalho.objects.filter(ciclo=ciclo).count())
print("  usuarios:   ", U.objects.count(), "(senha dos criados:", SENHA + ")")
print("  processo:   ", proc.numero, "-", proc.status_atual)
print("  movimentacao:", MovimentacaoProcessual.objects.filter(processo=proc).count())
