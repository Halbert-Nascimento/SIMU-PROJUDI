/**
 * Paginação client-side: mostra `porPagina` linhas por vez e esconde o resto.
 *
 * O bloco não pode mudar de altura ao trocar de página: a última quase sempre
 * tem menos linhas, e sem reserva o bloco encolhe e a página salta sob o cursor.
 * A reserva é feita de dois jeitos, porque os dois modelos de caixa reagem
 * diferente:
 *
 *   - listagem em <table>: linhas de preenchimento no <tbody>. `min-height` numa
 *     tabela não sobra embaixo — ela ESTICA as linhas existentes, e a linha
 *     solitária da última página acaba centralizada num bloco alto.
 *   - listagem em bloco (div): `min-height` medido no próprio contêiner.
 *
 * Em ambos, a reserva só existe enquanto houver mais de uma página: filtrar até
 * um resultado deve encolher a lista mesmo — o que não pode é encolher ao paginar.
 */
function criarPaginador(config) {
    let paginaAtual = 1;
    let alturaCheia = 0;   // altura do contêiner com uma página cheia, em px

    function getRowsFiltradas() {
        const todas = Array.from(document.querySelectorAll(config.rowSelector));
        return config.filtrarRows ? config.filtrarRows(todas) : todas;
    }

    /** Linhas de preenchimento já criadas, para poder refazê-las a cada render. */
    function limparPreenchimento(alvo) {
        if (!alvo) return;
        alvo.querySelectorAll('.paginador-preenchimento').forEach(r => r.remove());
    }

    /**
     * Reserva o espaço de uma página cheia. `visiveis` é quantas linhas a página
     * atual mostra; `corpo` é o pai das linhas (<tbody> ou a div da listagem).
     */
    function reservarEspaco(alvo, corpo, primeiraRow, totalPaginas, visiveis) {
        limparPreenchimento(alvo);

        if (!alvo || totalPaginas <= 1) {
            if (alvo) alvo.style.minHeight = '';
            return;
        }

        if (corpo && corpo.tagName === 'TBODY') {
            // Mede a altura, não conta linhas: numa listagem as linhas têm
            // alturas diferentes (uma com duas linhas de texto é bem mais alta
            // que uma com uma), então "faltam N linhas" não diz quanto espaço
            // falta. O preenchimento é uma linha só, da altura que sobra.
            if (visiveis === config.porPagina) {
                alturaCheia = corpo.offsetHeight;
            }
            const faltam = alturaCheia - corpo.offsetHeight;
            if (faltam > 0 && primeiraRow) {
                const colunas = primeiraRow.children.length || 1;
                const tr = document.createElement('tr');
                tr.className = 'paginador-preenchimento';
                tr.innerHTML = '<td colspan="' + colunas + '" style="height:'
                             + faltam + 'px"></td>';
                corpo.appendChild(tr);
            }
            return;
        }

        // contêiner em bloco: a altura vem de uma página cheia, medida de fato
        if (visiveis === config.porPagina) {
            alvo.style.minHeight = '';
            alturaCheia = alvo.offsetHeight;
        }
        if (alturaCheia) alvo.style.minHeight = alturaCheia + 'px';
    }

    function renderizar() {
        const rows = getRowsFiltradas();
        const total = rows.length;
        const totalPaginas = Math.ceil(total / config.porPagina) || 1;
        const tabela = document.getElementById(config.tabelaId);
        const msgVazio = document.getElementById(config.msgVazioId);
        const paginacao = document.getElementById(config.paginacaoId);

        // onde a reserva mora: por padrão o mesmo elemento da listagem
        const alvo = document.getElementById(config.alturaId || config.tabelaId);

        if (total === 0) {
            document.querySelectorAll(config.rowSelector).forEach(r => r.style.display = 'none');
            limparPreenchimento(alvo);
            if (alvo) alvo.style.minHeight = '';   // vazio não reserva espaço
            if (tabela) tabela.classList.add('hidden');
            if (msgVazio) msgVazio.classList.remove('hidden');
            if (paginacao) paginacao.classList.add('hidden');
            return;
        }

        if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;

        if (tabela) tabela.classList.remove('hidden');
        if (msgVazio) msgVazio.classList.add('hidden');

        const inicio = (paginaAtual - 1) * config.porPagina;
        const fim = inicio + config.porPagina;

        document.querySelectorAll(config.rowSelector).forEach(r => r.style.display = 'none');
        rows.forEach((r, i) => { r.style.display = (i >= inicio && i < fim) ? '' : 'none'; });

        const visiveis = Math.min(fim, total) - inicio;
        reservarEspaco(alvo, rows[0] && rows[0].parentElement, rows[inicio],
                       totalPaginas, visiveis);

        if (paginacao) {
            paginacao.classList.toggle('hidden', totalPaginas <= 1);
            document.getElementById(config.infoId).textContent =
                'Exibindo ' + (inicio + 1) + '–' + Math.min(fim, total) + ' de ' + total;
            document.getElementById(config.btnPrimeiraId).disabled = paginaAtual === 1;
            document.getElementById(config.btnAnteriorId).disabled = paginaAtual === 1;
            document.getElementById(config.btnProximaId).disabled = paginaAtual === totalPaginas;
            document.getElementById(config.btnUltimaId).disabled = paginaAtual === totalPaginas;

            const container = document.getElementById(config.paginasContainerId);
            container.innerHTML = '';
            for (let p = 1; p <= totalPaginas; p++) {
                const btn = document.createElement('button');
                btn.textContent = p;
                btn.className = p === paginaAtual
                    ? 'w-7 h-7 text-meta font-bold bg-navy text-white border border-navy'
                    : 'w-7 h-7 text-meta font-bold text-rotulo border border-transparent hover:border-contorno hover:text-acao transition-colors';
                btn.onclick = () => { paginaAtual = p; renderizar(); };
                container.appendChild(btn);
            }
        }
    }

    function mudarPagina(acao) {
        const totalPaginas = Math.ceil(getRowsFiltradas().length / config.porPagina) || 1;
        if (acao === 'primeira') paginaAtual = 1;
        else if (acao === 'anterior' && paginaAtual > 1) paginaAtual--;
        else if (acao === 'proxima' && paginaAtual < totalPaginas) paginaAtual++;
        else if (acao === 'ultima') paginaAtual = totalPaginas;
        renderizar();
    }

    function resetar() {
        paginaAtual = 1;
        renderizar();
    }

    return { renderizar, mudarPagina, resetar };
}
