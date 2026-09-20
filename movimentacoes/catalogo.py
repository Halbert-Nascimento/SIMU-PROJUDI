from __future__ import annotations

# Nomes do catálogo fechado de TipoMovimentacao (Ponto 3 do mapa) referenciados fora da
# migração de dados — fonte única, pra permissions.py e services.py não duplicarem a
# mesma string em dois lugares e correrem o risco de um rename (já aconteceu, Tarefa 2)
# atualizar um arquivo e esquecer o outro.

NOME_PROTOCOLO = "Protocolo da Petição Inicial"
NOME_CONTESTACAO = "Contestação"
NOME_MP_DEVE_INTERVIR_SIM = "MP Deve Intervir — Sim"
NOME_REDISTRIBUICAO = "Redistribuição"

NOMES_TRANSVERSAIS = {
    "Cancelamento / Tornar Sem Efeito",
    "Desentranhamento",
    "Juntada de Documentos",
    # Repete a cada troca de grupo no processo; fora daqui, a segunda redistribuição
    # seria lida como correção da primeira.
    NOME_REDISTRIBUICAO,
}
