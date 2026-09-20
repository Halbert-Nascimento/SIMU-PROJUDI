from __future__ import annotations

from dataclasses import dataclass

from ciclos.models import GrupoTrabalho

from .models import GrupoProcesso, PoloProcessual


class EstadoInvalidoError(ValueError):
    """Estado desejado que viola um grupo por papel, ou posição em conflito sem resolução."""


class Natureza:
    ATRIBUICAO = "atribuicao"
    SUBSTITUICAO = "substituicao"
    REMOCAO = "remocao"
    MUDANCA_DE_POSICAO = "mudanca_de_posicao"


@dataclass(frozen=True)
class Posicao:
    chave: str
    rotulo: str
    cargos: tuple[str, ...]
    tipo_polo: str | None


# Quem pode ocupar polo é regra de domínio, não dado de tabela: APA e MP são os únicos
# titulares de ação, e o catálogo de movimentações já amarra papel por código. Por isso as
# posições são declaradas aqui em vez de derivadas de CargoSimulacao. SC fica fora — o
# vínculo do cartório nasce na autuação e é ele que ancora os eventos nos autos.
POSICOES: tuple[Posicao, ...] = (
    Posicao("polo_ativo", "Polo ativo", ("APA", "MP"), PoloProcessual.TipoPolo.ATIVO),
    Posicao("polo_passivo", "Polo passivo", ("APP",), PoloProcessual.TipoPolo.PASSIVO),
    Posicao("ministerio_publico", "Ministério Público (interveniente)", ("MP",), None),
    Posicao("juiz", "Juiz", ("JZ",), None),
)

POSICOES_POR_CHAVE: dict[str, Posicao] = {posicao.chave: posicao for posicao in POSICOES}

# Onde um grupo já vinculado aparece quando não ocupa polo nenhum. O MP é o único cargo com
# duas posições possíveis, e é o polo que distingue titular de interveniente.
_POSICAO_PADRAO_DO_CARGO = {
    "APA": "polo_ativo",
    "APP": "polo_passivo",
    "MP": "ministerio_publico",
    "JZ": "juiz",
}


@dataclass(frozen=True)
class EstadoPosicao:
    posicao: Posicao
    grupos_vinculados: tuple[GrupoTrabalho, ...]
    grupos_disponiveis: tuple[GrupoTrabalho, ...]

    @property
    def grupo(self) -> GrupoTrabalho | None:
        """O ocupante da posição, ou None quando está vazia ou em conflito."""
        return self.grupos_vinculados[0] if len(self.grupos_vinculados) == 1 else None

    @property
    def em_conflito(self) -> bool:
        return len(self.grupos_vinculados) > 1

    @property
    def pendente(self) -> bool:
        return not self.grupos_vinculados

    @property
    def indisponivel(self) -> bool:
        return not self.grupos_disponiveis and not self.grupos_vinculados

    @property
    def opcoes(self) -> tuple[GrupoTrabalho, ...]:
        """O que a tela oferece para atribuir ou substituir: quem já está aqui não é opção."""
        vinculados = {grupo.pk for grupo in self.grupos_vinculados}
        return tuple(grupo for grupo in self.grupos_disponiveis if grupo.pk not in vinculados)


@dataclass(frozen=True)
class Alteracao:
    natureza: str
    posicao: Posicao
    grupo_anterior: GrupoTrabalho | None = None
    grupo_novo: GrupoTrabalho | None = None
    posicao_origem: Posicao | None = None


@dataclass(frozen=True)
class Plano:
    alteracoes: tuple[Alteracao, ...]
    vinculos_a_criar: tuple[GrupoTrabalho, ...]
    vinculos_a_remover: tuple[GrupoTrabalho, ...]
    donos_de_polo: dict[str, GrupoTrabalho | None]

    @property
    def vazio(self) -> bool:
        return not self.alteracoes


def estado_posicoes_do_processo(processo) -> list[EstadoPosicao]:
    """
    Estado das quatro posições deste processo, em três consultas.

    A posição de cada grupo sai do **vínculo**, não do polo: processo ainda "Protocolado" tem
    o grupo que peticionou vinculado sem polo nenhum, e ler pelo polo o faria desaparecer da
    tela (ver achado 2 de 01_implementacoes/07).
    """
    vinculados = [
        grupo_processo.grupo
        for grupo_processo in (
            GrupoProcesso.objects
            .filter(processo=processo)
            .select_related("grupo__cargo_simulacao")
            .order_by("grupo__nome", "pk")
        )
    ]
    donos_por_polo: dict[str, set[int]] = {}
    for tipo_polo, grupo_id in (
        PoloProcessual.objects
        .filter(processo=processo, grupo__isnull=False)
        .values_list("tipo_polo", "grupo_id")
    ):
        donos_por_polo.setdefault(tipo_polo, set()).add(grupo_id)

    grupos_do_ciclo = list(
        GrupoTrabalho.objects
        .filter(ciclo_id=processo.ciclo_id)
        .select_related("cargo_simulacao")
        .order_by("nome")
    )

    ocupantes: dict[str, list[GrupoTrabalho]] = {posicao.chave: [] for posicao in POSICOES}
    for grupo in vinculados:
        chave = _chave_da_posicao(grupo, donos_por_polo)
        if chave:
            ocupantes[chave].append(grupo)

    return [
        EstadoPosicao(
            posicao=posicao,
            grupos_vinculados=tuple(ocupantes[posicao.chave]),
            grupos_disponiveis=tuple(
                grupo for grupo in grupos_do_ciclo
                if grupo.cargo_simulacao.cod in posicao.cargos
            ),
        )
        for posicao in POSICOES
    ]


def _chave_da_posicao(grupo, donos_por_polo) -> str | None:
    """Polo ocupado decide; sem polo, decide o papel. SC devolve None — está fora da tela."""
    for posicao in POSICOES:
        if posicao.tipo_polo and grupo.pk in donos_por_polo.get(posicao.tipo_polo, ()):
            return posicao.chave
    return _POSICAO_PADRAO_DO_CARGO.get(grupo.cargo_simulacao.cod)


def planejar_alteracoes(estados, desejado) -> Plano:
    """
    Diferença entre o estado atual das posições e o desejado.

    `desejado` mapeia chave de posição para o `GrupoTrabalho` que deve ocupá-la, ou None para
    deixá-la vazia. Posição ausente do dicionário fica como está — exceto quando está em
    conflito, caso em que "como está" é ambíguo e a resolução tem que ser explícita.
    """
    final: dict[str, GrupoTrabalho | None] = {}
    for estado in estados:
        chave = estado.posicao.chave
        if chave in desejado:
            final[chave] = desejado[chave]
        elif estado.em_conflito:
            raise EstadoInvalidoError(
                f'A posição "{estado.posicao.rotulo}" tem mais de um grupo vinculado e precisa '
                "de resolução explícita antes de qualquer alteração."
            )
        else:
            final[chave] = estado.grupo

    _garantir_um_grupo_por_papel(final)

    alteracoes = _alteracoes(estados, final)

    antes = {grupo.pk: grupo for estado in estados for grupo in estado.grupos_vinculados}
    depois = {grupo.pk: grupo for grupo in final.values() if grupo is not None}

    return Plano(
        alteracoes=tuple(alteracoes),
        vinculos_a_criar=tuple(depois[pk] for pk in depois if pk not in antes),
        vinculos_a_remover=tuple(antes[pk] for pk in antes if pk not in depois),
        donos_de_polo={
            posicao.tipo_polo: final[posicao.chave]
            for posicao in POSICOES
            if posicao.tipo_polo
        },
    )


def _garantir_um_grupo_por_papel(final) -> None:
    """
    Nenhum papel ocupa duas posições. Só o MP consegue tentar — polo ativo e interveniente
    aceitam o cargo dele —, seja com dois grupos diferentes, seja com o mesmo em ambas, que
    seria titular e fiscal da lei ao mesmo tempo.
    """
    posicoes_por_cargo: dict[str, list[str]] = {}
    for chave, grupo in final.items():
        if grupo is None:
            continue
        cod = grupo.cargo_simulacao.cod
        posicoes_por_cargo.setdefault(cod, []).append(POSICOES_POR_CHAVE[chave].rotulo)

    for cod, rotulos in posicoes_por_cargo.items():
        if len(rotulos) > 1:
            raise EstadoInvalidoError(
                f"O papel {cod} não pode ocupar mais de uma posição no mesmo processo "
                f"({', '.join(rotulos)})."
            )


def _alteracoes(estados, final) -> list[Alteracao]:
    """
    Classifica o diff em saídas e entradas por posição, e depois casa uma com a outra.

    O casamento entre posições diferentes vem primeiro de propósito: um grupo que troca de
    posição continua no processo, e descrevê-lo como "removido" numa linha e "atribuído" em
    outra daria a entender nos autos que ele saiu. É o caso do MP entre titular e
    interveniente.
    """
    saidas: list[tuple[Posicao, GrupoTrabalho]] = []
    entradas: list[tuple[Posicao, GrupoTrabalho]] = []
    for estado in estados:
        novo = final[estado.posicao.chave]
        for grupo in estado.grupos_vinculados:
            if novo is None or grupo.pk != novo.pk:
                saidas.append((estado.posicao, grupo))
        if novo is not None and all(novo.pk != grupo.pk for grupo in estado.grupos_vinculados):
            entradas.append((estado.posicao, novo))

    alteracoes: list[Alteracao] = []

    for entrada in list(entradas):
        destino, grupo = entrada
        origem = next((saida for saida in saidas if saida[1].pk == grupo.pk), None)
        if origem is None:
            continue
        saidas.remove(origem)
        entradas.remove(entrada)
        alteracoes.append(Alteracao(
            natureza=Natureza.MUDANCA_DE_POSICAO, posicao=destino,
            posicao_origem=origem[0], grupo_novo=grupo,
        ))

    for entrada in list(entradas):
        destino, grupo_novo = entrada
        anterior = next((saida for saida in saidas if saida[0].chave == destino.chave), None)
        if anterior is None:
            continue
        saidas.remove(anterior)
        entradas.remove(entrada)
        alteracoes.append(Alteracao(
            natureza=Natureza.SUBSTITUICAO, posicao=destino,
            grupo_anterior=anterior[1], grupo_novo=grupo_novo,
        ))

    alteracoes += [
        Alteracao(natureza=Natureza.REMOCAO, posicao=posicao, grupo_anterior=grupo)
        for posicao, grupo in saidas
    ]
    alteracoes += [
        Alteracao(natureza=Natureza.ATRIBUICAO, posicao=posicao, grupo_novo=grupo)
        for posicao, grupo in entradas
    ]

    ordem = {posicao.chave: indice for indice, posicao in enumerate(POSICOES)}
    return sorted(alteracoes, key=lambda alteracao: ordem[alteracao.posicao.chave])


def descrever_alteracoes(plano) -> str:
    """Texto que vai para `descricao_evento` da movimentação — e que a tela mostra antes de gravar."""
    partes: list[str] = []
    for alteracao in plano.alteracoes:
        rotulo = alteracao.posicao.rotulo
        if alteracao.natureza == Natureza.ATRIBUICAO:
            partes.append(f'{rotulo}: "{alteracao.grupo_novo.nome}" atribuído.')
        elif alteracao.natureza == Natureza.SUBSTITUICAO:
            partes.append(
                f'{rotulo}: "{alteracao.grupo_anterior.nome}" substituído por '
                f'"{alteracao.grupo_novo.nome}".'
            )
        elif alteracao.natureza == Natureza.REMOCAO:
            partes.append(f'{rotulo}: "{alteracao.grupo_anterior.nome}" removido.')
        elif alteracao.natureza == Natureza.MUDANCA_DE_POSICAO:
            partes.append(
                f'"{alteracao.grupo_novo.nome}" passa de {alteracao.posicao_origem.rotulo} '
                f'para {rotulo}.'
            )
    return " ".join(partes)
