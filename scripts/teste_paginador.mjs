/**
 * Teste de comportamento do paginador (static/js/paginador.js).
 *
 *     node scripts/teste_paginador.mjs
 *
 * DOM minimo escrito a mao — o projeto nao tem jsdom nem runner de JS.
 *
 * A parte final cobre a RESERVA DE ALTURA: bloco paginado nao pode encolher ao
 * trocar para uma pagina com menos linhas. Esse defeito ja apareceu duas vezes,
 * em telas diferentes; ver a secao "Componente com paginacao" do CLAUDE.md.
 * Ao criar um paginador novo, acrescente o caso aqui.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(fileURLToPath(import.meta.url), '../..');

// ── DOM minimo ───────────────────────────────────────────────────────────────
class ClassList {
    constructor(el) { this.el = el; }
    get _s() { return new Set(this.el.className.split(/\s+/).filter(Boolean)); }
    _w(s) { this.el.className = [...s].join(' '); }
    add(...c) { const s = this._s; c.forEach(x => s.add(x)); this._w(s); }
    remove(...c) { const s = this._s; c.forEach(x => s.delete(x)); this._w(s); }
    contains(c) { return this._s.has(c); }
    toggle(c, force) {
        const alvo = force === undefined ? !this.contains(c) : force;
        if (alvo) this.add(c); else this.remove(c);
        return alvo;
    }
}

class El {
    constructor(tag) {
        this.tagName = tag.toUpperCase();
        this.className = '';
        this.id = '';
        this.style = {};
        this.dataset = {};
        this.children = [];
        this.textContent = '';
        this.disabled = false;
        this.onclick = null;
        this._html = '';
    }
    get classList() { return new ClassList(this); }
    get parentElement() { return this._pai || null; }
    remove() {
        const pai = this._pai;
        if (pai) pai.children = pai.children.filter(c => c !== this);
    }
    /** Só o seletor de classe, que é o que o paginador usa aqui dentro. */
    querySelectorAll(sel) {
        const cls = /^\.([\w-]+)$/.exec(sel);
        if (!cls) throw new Error('seletor nao suportado: ' + sel);
        return this.children.filter(c => c.classList.contains(cls[1]));
    }
    /**
     * Altura simulada. Respeita `style.height` de cada filho — as linhas de uma
     * listagem real NAO tem todas a mesma altura, e foi supor isso que quebrou
     * a primeira versao do preenchimento.
     */
    get offsetHeight() {
        return this.children
            .filter(c => c.style.display !== 'none')
            .reduce((h, c) => h + (parseInt(c.style.height, 10)
                                   || parseInt(c._alturaLinha, 10) || 40), 0);
    }
    appendChild(c) { c._pai = this; this.children.push(c); return c; }
    set innerHTML(h) {
        this._html = h;
        // <td style="height:Npx"> define a altura da <tr> que o contem
        const alt = /<td[^>]*style="height:(\d+)px"/.exec(h);
        if (alt) this.style.height = alt[1] + 'px';
        this.children = parseLinhas(h);
        this.children.forEach(c => { c._pai = this; });
    }
    get innerHTML() { return this._html; }
}

const porId = new Map();
const todosEls = [];

/** Le so as <div> de primeiro nivel do fragmento: class e data-i. */
function parseLinhas(html) {
    const out = [];
    let prof = 0;
    for (const t of html.matchAll(/<(\/?)div\b([^>]*)>/g)) {
        if (t[1] === '/') { prof--; continue; }
        if (prof === 0) {
            const el = new El('div');
            const cls = /class="([^"]*)"/.exec(t[2]);
            const di = /data-i="([^"]*)"/.exec(t[2]);
            const alt = /data-altura="([^"]*)"/.exec(t[2]);
            el.className = cls ? cls[1] : '';
            if (di) el.dataset.i = di[1];
            if (alt) el._alturaLinha = alt[1];
            out.push(el);
        }
        prof++;
    }
    return out;
}

globalThis.document = {
    getElementById: (id) => porId.get(id) || null,
    querySelectorAll: (sel) => {
        const m = /^#([\w-]+)\s+\.([\w-]+)$/.exec(sel);
        if (m) {
            const cont = porId.get(m[1]);
            return cont ? cont.children.filter(c => c.classList.contains(m[2])) : [];
        }
        throw new Error('seletor nao suportado: ' + sel);
    },
    createElement: (t) => new El(t),
};

function novoEl(id, className = '') {
    const e = new El('div');
    e.id = id;
    e.className = className;
    porId.set(id, e);
    todosEls.push(e);
    return e;
}

const listaAlunos = novoEl('lista-alunos-disponiveis', 'flex-1 min-h-0 overflow-y-auto px-3');
const alunosVazio = novoEl('alunos-vazio', 'hidden');
const pagAlunos = novoEl('paginacao-alunos', 'hidden');
novoEl('paginacao-alunos-info');
novoEl('paginacao-alunos-paginas');
for (const b of ['primeira', 'anterior', 'proxima', 'ultima']) novoEl('btn-alu-' + b);

const listaMembros = novoEl('lista-membros', 'flex-1 min-h-0 overflow-y-auto p-3');
const membrosVazio = novoEl('membros-vazio', 'hidden');
const pagMembros = novoEl('paginacao-membros', 'hidden');
novoEl('paginacao-membros-info');
novoEl('paginacao-membros-paginas');
for (const b of ['primeira', 'anterior', 'proxima', 'ultima']) novoEl('btn-mem-' + b);

novoEl('membros-count');
novoEl('alunos-sem-grupo-count');

// ── carrega o paginador de verdade ───────────────────────────────────────────
const src = fs.readFileSync(path.join(REPO, 'templates/static/js/paginador.js'), 'utf8');
const criarPaginador = new Function(src + '; return criarPaginador;')();

// ── replica a fiação do template ─────────────────────────────────────────────
let alunosData = [];
let alunoBusca = '';

const paginadorAlunos = criarPaginador({
    rowSelector: '#lista-alunos-disponiveis .aluno-row',
    porPagina: 6,
    tabelaId: 'lista-alunos-disponiveis',
    msgVazioId: 'alunos-vazio',
    paginacaoId: 'paginacao-alunos',
    infoId: 'paginacao-alunos-info',
    paginasContainerId: 'paginacao-alunos-paginas',
    btnPrimeiraId: 'btn-alu-primeira',
    btnAnteriorId: 'btn-alu-anterior',
    btnProximaId: 'btn-alu-proxima',
    btnUltimaId: 'btn-alu-ultima',
    filtrarRows: (todas) => !alunoBusca ? todas : todas.filter(r => {
        const a = alunosData[Number(r.dataset.i)];
        return a && (a.nome.toLowerCase().includes(alunoBusca)
                  || (a.email || '').toLowerCase().includes(alunoBusca));
    }),
});

const paginadorMembros = criarPaginador({
    rowSelector: '#lista-membros .membro-row',
    porPagina: 6,
    tabelaId: 'lista-membros',
    msgVazioId: 'membros-vazio',
    paginacaoId: 'paginacao-membros',
    infoId: 'paginacao-membros-info',
    paginasContainerId: 'paginacao-membros-paginas',
    btnPrimeiraId: 'btn-mem-primeira',
    btnAnteriorId: 'btn-mem-anterior',
    btnProximaId: 'btn-mem-proxima',
    btnUltimaId: 'btn-mem-ultima',
});

function renderizarDisponiveis() {
    document.getElementById('alunos-sem-grupo-count').textContent = alunosData.length;
    listaAlunos.innerHTML = alunosData.map((a, i) =>
        `<div class="aluno-row border-b" data-i="${i}"><div class="x"></div></div>`).join('');
    paginadorAlunos.resetar();
}

function renderizarMembros(membros) {
    document.getElementById('membros-count').textContent = membros.length;
    listaMembros.innerHTML = membros.map(() =>
        `<div class="membro-row bg-white mb-2"><div class="y"></div></div>`).join('');
    paginadorMembros.resetar();
}

function filtrarAlunos(texto) {
    alunoBusca = (texto || '').toLowerCase();
    alunosVazio.textContent = alunoBusca
        ? 'Nenhum aluno encontrado.'
        : 'Nenhum aluno disponível para este ciclo.';
    paginadorAlunos.resetar();
}

// ── asserções ────────────────────────────────────────────────────────────────
let falhas = 0;
const ok = (cond, msg) => {
    console.log((cond ? '[ ok  ] ' : '[FALHA] ') + msg);
    if (!cond) falhas++;
};
const visiveis = (el, cls) =>
    el.children.filter(c => c.classList.contains(cls) && c.style.display !== 'none').length;

alunosData = Array.from({ length: 20 }, (_, i) => ({
    id: i, nome: 'Aluno ' + i, email: 'aluno' + i + '@iesgo.edu.br',
}));
renderizarDisponiveis();
ok(visiveis(listaAlunos, 'aluno-row') === 6, '20 alunos -> 6 linhas visíveis (a página não estica)');
ok(!pagAlunos.classList.contains('hidden'), '20 alunos -> controles de paginação visíveis');
ok(document.getElementById('paginacao-alunos-info').textContent === 'Exibindo 1–6 de 20',
   'info: "Exibindo 1–6 de 20"');
ok(document.getElementById('paginacao-alunos-paginas').children.length === 4,
   '20 alunos / 6 por página -> 4 botões de página');

paginadorAlunos.mudarPagina('ultima');
ok(visiveis(listaAlunos, 'aluno-row') === 2, 'última página -> 2 linhas (20 = 6+6+6+2)');
ok(document.getElementById('btn-alu-proxima').disabled === true, 'última página -> "próxima" desabilitado');

filtrarAlunos('aluno7@');
ok(visiveis(listaAlunos, 'aluno-row') === 1, 'busca por e-mail -> 1 resultado');
ok(pagAlunos.classList.contains('hidden'), '1 resultado -> paginação escondida');
ok(alunosVazio.textContent === 'Nenhum aluno encontrado.', 'texto do vazio troca para "Nenhum aluno encontrado."');

filtrarAlunos('aluno 1');
ok(visiveis(listaAlunos, 'aluno-row') === 6, 'busca por nome "aluno 1" -> 11 achados, 6 na página');

filtrarAlunos('zzz');
ok(visiveis(listaAlunos, 'aluno-row') === 0, 'busca sem resultado -> nenhuma linha');
ok(!alunosVazio.classList.contains('hidden'), 'busca sem resultado -> estado vazio visível');
ok(listaAlunos.classList.contains('hidden'), 'busca sem resultado -> lista escondida');

filtrarAlunos('');
ok(visiveis(listaAlunos, 'aluno-row') === 6, 'limpar busca -> 6 linhas de novo');
ok(alunosVazio.classList.contains('hidden'), 'limpar busca -> estado vazio escondido');
ok(!listaAlunos.classList.contains('hidden'), 'limpar busca -> lista visível de novo');
ok(document.getElementById('paginacao-alunos-info').textContent === 'Exibindo 1–6 de 20',
   'limpar busca -> volta para a página 1');

renderizarMembros([]);
ok(!membrosVazio.classList.contains('hidden'), 'grupo sem membros -> estado vazio visível');
ok(pagMembros.classList.contains('hidden'), 'grupo sem membros -> paginação escondida');

renderizarMembros(Array.from({ length: 9 }, (_, i) => ({ id: i })));
ok(visiveis(listaMembros, 'membro-row') === 6, '9 membros -> 6 visíveis');
ok(document.getElementById('membros-count').textContent === 9, 'contador do cabeçalho mostra 9');
paginadorMembros.mudarPagina('proxima');
ok(visiveis(listaMembros, 'membro-row') === 3, 'segunda página -> 3 membros');

renderizarMembros(Array.from({ length: 9 }, (_, i) => ({ id: i })));
ok(document.getElementById('paginacao-membros-info').textContent === 'Exibindo 1–6 de 9',
   'trocar de grupo -> volta para a página 1');

// ── Reserva de altura: o bloco não pode encolher ao trocar de página ────────
// (o defeito que apareceu em gerenciar_grupos e depois em painel_administrativo)
alunosData = Array.from({ length: 20 }, (_, i) => ({
    id: i, nome: 'Aluno ' + i, email: 'aluno' + i + '@iesgo.edu.br',
}));
renderizarDisponiveis();
const alturaPagina1 = listaAlunos.style.minHeight;
ok(alturaPagina1 === '240px', `página cheia reserva a própria altura (${alturaPagina1})`);

paginadorAlunos.mudarPagina('ultima');   // 2 linhas de 20
ok(visiveis(listaAlunos, 'aluno-row') === 2, 'última página mostra 2 linhas');
ok(listaAlunos.style.minHeight === alturaPagina1,
   'última página mantém a altura reservada — o bloco não encolhe');

filtrarAlunos('aluno7@');   // 1 resultado: uma página só
ok(listaAlunos.style.minHeight === '',
   'uma página só dispensa a reserva (a lista pode encolher com o filtro)');

filtrarAlunos('zzz');       // nenhum resultado
ok(listaAlunos.style.minHeight === '', 'lista vazia não reserva espaço');

filtrarAlunos('');
ok(listaAlunos.style.minHeight === alturaPagina1, 'limpar o filtro devolve a reserva');

renderizarMembros(Array.from({ length: 3 }, (_, i) => ({ id: i })));
ok(listaMembros.style.minHeight === '',
   '3 membros com 6 por página: uma página só, sem reserva');

// ── Listagem em <table>: a reserva vira linha de preenchimento ─────────────
// Numa tabela, min-height estica as linhas em vez de sobrar espaco embaixo: a
// linha unica da ultima pagina fica centralizada num bloco alto. Por isso o
// paginador completa a pagina com <tr> vazios.
const tbody = novoEl('tbody-ciclos', '');
tbody.tagName = 'TBODY';
const tabelaCiclos = novoEl('tabela-ciclos', '');
novoEl('ciclos-vazio', 'hidden');
const pagCiclos = novoEl('paginacao-ciclos', 'hidden');
novoEl('paginacao-ciclos-info');
novoEl('paginacao-ciclos-paginas');
for (const b of ['primeira', 'anterior', 'proxima', 'ultima']) novoEl('btn-ciclo-' + b);

const paginadorCiclos = criarPaginador({
    rowSelector: '#tbody-ciclos .ciclo-row',
    porPagina: 5,
    tabelaId: 'tbody-ciclos',
    msgVazioId: 'ciclos-vazio',
    paginacaoId: 'paginacao-ciclos',
    infoId: 'paginacao-ciclos-info',
    paginasContainerId: 'paginacao-ciclos-paginas',
    btnPrimeiraId: 'btn-ciclo-primeira',
    btnAnteriorId: 'btn-ciclo-anterior',
    btnProximaId: 'btn-ciclo-proxima',
    btnUltimaId: 'btn-ciclo-ultima',
});

// 11 ciclos, 5 por pagina: a ultima pagina tem 1 (o caso da captura de tela)
// 60px: linha com duas linhas de texto (nome + semestre/responsavel), como na
// tabela de ciclos de verdade. O preenchimento tem que repor ISSO, e nao 40px.
tbody.innerHTML = Array.from({ length: 11 }, () =>
    '<div class="ciclo-row" data-altura="60"><div class="c1"></div><div class="c2"></div>' +
    '<div class="c3"></div><div class="c4"></div></div>').join('');
paginadorCiclos.resetar();
const alturaCheiaTbody = tbody.offsetHeight;
ok(alturaCheiaTbody === 300, `página cheia = 5 linhas de 60px (${alturaCheiaTbody})`);

const preench = () => tbody.children.filter(c => c.classList.contains('paginador-preenchimento')).length;
ok(preench() === 0, 'página cheia não cria linha de preenchimento');
ok(tbody.style.minHeight === undefined || tbody.style.minHeight === '',
   'tabela não usa min-height (ele esticaria as linhas)');

paginadorCiclos.mudarPagina('ultima');
ok(visiveis(tbody, 'ciclo-row') === 1, 'última página mostra 1 de 11');
ok(preench() === 1, 'e completa com uma linha de preenchimento');
ok(tbody.offsetHeight === alturaCheiaTbody,
   `altura do corpo continua ${alturaCheiaTbody}px — o bloco não muda de tamanho`);
// sem `?.` o teste ESTOURA quando o preenchimento nao existe, e as asseroes
// seguintes nunca rodam — foi o que escondeu uma falha ao reintroduzir o defeito
const filler = tbody.children.find(c => c.classList.contains('paginador-preenchimento'));
ok(filler?.style.height === '240px',
   `o preenchimento repõe a altura que falta, não um número de linhas (${filler?.style.height})`);
ok(tbody.style.minHeight === undefined || tbody.style.minHeight === '',
   'ainda sem min-height: o espaço vem das linhas, no fim da lista');

paginadorCiclos.mudarPagina('primeira');
ok(preench() === 0, 'voltar para uma página cheia remove o preenchimento');

// ── Listagem reconstruida a cada filtro (minhas_notas) ─────────────────────
// Aqui o filtro NAO passa por `filtrarRows`: a tela reescreve o <tbody> inteiro
// com as linhas do filtro e chama resetar(). O paginador tem que remedir a
// pagina cheia a cada reconstrucao — se ele guardasse a altura da lista antiga,
// filtrar deixaria a reserva errada.
const avalBody = novoEl('avalBody', '');
avalBody.tagName = 'TBODY';
novoEl('tabela-avaliacoes', '');
novoEl('avaliacoes-vazio', 'hidden');
const pagAval = novoEl('paginacao-avaliacoes', 'hidden');
novoEl('paginacao-avaliacoes-info');
novoEl('paginacao-avaliacoes-paginas');
for (const b of ['primeira', 'anterior', 'proxima', 'ultima']) novoEl('btn-aval-' + b);

const paginadorAvaliacoes = criarPaginador({
    rowSelector: '#avalBody .aval-row',
    porPagina: 10,
    tabelaId: 'tabela-avaliacoes',
    msgVazioId: 'avaliacoes-vazio',
    paginacaoId: 'paginacao-avaliacoes',
    infoId: 'paginacao-avaliacoes-info',
    paginasContainerId: 'paginacao-avaliacoes-paginas',
    btnPrimeiraId: 'btn-aval-primeira',
    btnAnteriorId: 'btn-aval-anterior',
    btnProximaId: 'btn-aval-proxima',
    btnUltimaId: 'btn-aval-ultima',
});

// 60px: a linha tem celula dupla (movimentacao + numero do processo)
function renderAvaliacoes(quantas) {
    avalBody.innerHTML = Array.from({ length: quantas }, () =>
        '<div class="aval-row" data-altura="60"><div class="c1"></div></div>').join('');
    paginadorAvaliacoes.resetar();
}

renderAvaliacoes(23);
ok(visiveis(avalBody, 'aval-row') === 10, '23 avaliações -> 10 na página');
ok(document.getElementById('paginacao-avaliacoes-info').textContent === 'Exibindo 1–10 de 23',
   'info: "Exibindo 1–10 de 23"');
const alturaCheiaAval = avalBody.offsetHeight;
ok(alturaCheiaAval === 600, `página cheia = 10 linhas de 60px (${alturaCheiaAval})`);

paginadorAvaliacoes.mudarPagina('ultima');
ok(visiveis(avalBody, 'aval-row') === 3, 'última página -> 3 de 23');
ok(avalBody.offsetHeight === alturaCheiaAval,
   'última página mantém a altura da página cheia');

renderAvaliacoes(4);   // filtro "Sem nota": a tela reescreve o corpo inteiro
ok(visiveis(avalBody, 'aval-row') === 4, 'filtrar para 4 -> as 4 aparecem');
ok(pagAval.classList.contains('hidden'), '4 avaliações -> uma página só, sem controles');
ok(avalBody.children.filter(c => c.classList.contains('paginador-preenchimento')).length === 0,
   'uma página só não reserva espaço — filtrar pode encolher a lista');

renderAvaliacoes(23);  // limpar o filtro
ok(document.getElementById('paginacao-avaliacoes-info').textContent === 'Exibindo 1–10 de 23',
   'limpar o filtro volta para a página 1');

renderAvaliacoes(0);
ok(!document.getElementById('avaliacoes-vazio').classList.contains('hidden'),
   'filtro sem resultado -> estado vazio visível');


console.log(falhas ? `\n${falhas} falha(s)` : '\ntudo passou');
process.exit(falhas ? 1 : 0);
