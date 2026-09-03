function criarPaginador(config) {
    let paginaAtual = 1;

    function getRowsFiltradas() {
        const todas = Array.from(document.querySelectorAll(config.rowSelector));
        return config.filtrarRows ? config.filtrarRows(todas) : todas;
    }

    function renderizar() {
        const rows = getRowsFiltradas();
        const total = rows.length;
        const totalPaginas = Math.ceil(total / config.porPagina) || 1;
        const tabela = document.getElementById(config.tabelaId);
        const msgVazio = document.getElementById(config.msgVazioId);
        const paginacao = document.getElementById(config.paginacaoId);

        if (total === 0) {
            document.querySelectorAll(config.rowSelector).forEach(r => r.style.display = 'none');
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
