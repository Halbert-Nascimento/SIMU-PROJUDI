/**
 * Teste de comportamento dos avisos (static/js/toast.js).
 *
 *     node scripts/teste_toast.mjs
 *
 * DOM mínimo escrito à mão e relógio controlado: a remoção de um aviso é adiada,
 * e é nesse intervalo que a pilha cheia precisa continuar respondendo.
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(fileURLToPath(import.meta.url), '../..');
const FONTE = fs.readFileSync(path.join(REPO, 'templates/static/js/toast.js'), 'utf8');

class No {
    constructor() {
        this.children = [];
        this.parentNode = null;
        this.className = '';
        this.style = {};
        const classes = new Set();
        this.classList = {
            add: c => classes.add(c),
            remove: c => classes.delete(c),
            contains: c => classes.has(c),
        };
    }
    get firstChild() { return this.children[0] || null; }
    get lastElementChild() { return this.children[this.children.length - 1] || null; }
    get offsetWidth() { return 0; }
    setAttribute() {}
    addEventListener() {}
    appendChild(no) { no.parentNode = this; this.children.push(no); return no; }
    insertBefore(no, antes) {
        no.parentNode = this;
        const i = this.children.indexOf(antes);
        this.children.splice(i < 0 ? this.children.length : i, 0, no);
        return no;
    }
    removeChild(no) {
        this.children = this.children.filter(f => f !== no);
        no.parentNode = null;
        return no;
    }
}

function criarTela() {
    const pilha = new No();
    const agendados = new Map();
    let proximo = 0;
    let agora = 0;
    const contexto = vm.createContext({
        document: { getElementById: () => pilha, createElement: () => new No(), body: new No() },
        setTimeout: (fn, ms) => { agendados.set(++proximo, { fn, em: agora + ms }); return proximo; },
        clearTimeout: id => agendados.delete(id),
    });
    vm.runInContext(FONTE, contexto);
    return {
        pilha,
        // timeout do vm: um laço sem fim vira erro em vez de travar o teste
        mostrar: texto => vm.runInContext(`showToast(${JSON.stringify(texto)})`, contexto, { timeout: 500 }),
        avancar(ms) {
            agora += ms;
            for (const [id, t] of [...agendados]) {
                if (t.em <= agora && agendados.delete(id)) t.fn();
            }
        },
        fecharMaisNovo: () => vm.runInContext('removerToast(document.getElementById().children[0])', contexto),
        textos: () => pilha.children.map(t => t.children[0].children[1].children[1].textContent),
    };
}

let falhas = 0;
function conferir(nome, condicao, detalhe = '') {
    if (!condicao) falhas++;
    console.log(`[${condicao ? ' ok ' : 'FALHA'}] ${nome}${condicao ? '' : ` — ${detalhe}`}`);
}

function rodar(nome, cenario) {
    try {
        cenario(criarTela());
    } catch (erro) {
        conferir(nome, false, erro.message);
    }
}

rodar('quarto aviso seguido não trava a tela', tela => {
    ['um', 'dois', 'três', 'quatro'].forEach(t => tela.mostrar(t));
    tela.avancar(200);
    conferir('quarto aviso seguido não trava a tela',
        JSON.stringify(tela.textos()) === JSON.stringify(['quatro', 'três', 'dois']),
        JSON.stringify(tela.textos()));
});

rodar('rajada mantém só os três mais novos', tela => {
    for (let i = 1; i <= 10; i++) tela.mostrar(String(i));
    tela.avancar(200);
    conferir('rajada mantém só os três mais novos',
        JSON.stringify(tela.textos()) === JSON.stringify(['10', '9', '8']),
        JSON.stringify(tela.textos()));
});

rodar('o aviso excedente só sai depois da animação', tela => {
    ['um', 'dois', 'três', 'quatro'].forEach(t => tela.mostrar(t));
    conferir('o aviso excedente só sai depois da animação', tela.pilha.children.length === 4,
        `${tela.pilha.children.length} na pilha`);
});

rodar('fechar um aviso não faz o mais antigo sair no lugar dele', tela => {
    ['um', 'dois', 'três'].forEach(t => tela.mostrar(t));
    tela.fecharMaisNovo();
    tela.mostrar('quatro');
    tela.avancar(200);
    conferir('fechar um aviso não faz o mais antigo sair no lugar dele',
        JSON.stringify(tela.textos()) === JSON.stringify(['quatro', 'dois', 'um']),
        JSON.stringify(tela.textos()));
});

rodar('até três avisos ficam e somem no tempo próprio', tela => {
    ['um', 'dois'].forEach(t => tela.mostrar(t));
    tela.avancar(200);
    const antes = tela.pilha.children.length;
    tela.avancar(2600);
    tela.avancar(200);
    conferir('até três avisos ficam e somem no tempo próprio',
        antes === 2 && tela.pilha.children.length === 0,
        `antes ${antes}, depois ${tela.pilha.children.length}`);
});

console.log(falhas ? `\n${falhas} falha(s)` : '\ntudo passou');
process.exit(falhas ? 1 : 0);
