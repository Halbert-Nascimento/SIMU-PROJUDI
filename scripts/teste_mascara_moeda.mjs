/**
 * Teste de comportamento da máscara monetária (static/js/mascara_moeda.js).
 *
 *     node scripts/teste_mascara_moeda.mjs
 *
 * DOM mínimo escrito à mão — o projeto não tem jsdom nem runner de JS.
 * A máscara é de caixa eletrônico: o dígito entra pelos centavos e empurra o
 * valor para a esquerda. Digitar 1 dá R$ 0,01; digitar 2000 depois dá R$ 120,00.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(fileURLToPath(import.meta.url), '../..');

// ── DOM mínimo ───────────────────────────────────────────────────────────────
const porId = new Map();

class Campo {
    constructor(id, value = '') {
        this.id = id;
        this.value = value;
        this.ouvintes = {};
        porId.set(id, this);
    }
    addEventListener(evento, fn) {
        (this.ouvintes[evento] = this.ouvintes[evento] || []).push(fn);
    }
    /** Simula uma tecla; devolve se o handler pediu preventDefault. */
    teclar(key) {
        let barrou = false;
        const e = { key, preventDefault: () => { barrou = true; } };
        (this.ouvintes.keydown || []).forEach(fn => fn(e));
        return barrou;
    }
    colar() {
        let barrou = false;
        (this.ouvintes.paste || []).forEach(fn => fn({ preventDefault: () => { barrou = true; } }));
        return barrou;
    }
}

globalThis.document = { getElementById: (id) => porId.get(id) || null };

const src = fs.readFileSync(path.join(REPO, 'templates/static/js/mascara_moeda.js'), 'utf8');
const criarMascaraMoeda = new Function(src + '; return criarMascaraMoeda;')();

// ── asserções ────────────────────────────────────────────────────────────────
let falhas = 0;
const ok = (cond, msg) => {
    console.log((cond ? '[ ok  ] ' : '[FALHA] ') + msg);
    if (!cond) falhas++;
};
/** O toLocaleString usa espaço não separável no "R$ "; normaliza para comparar. */
const visto = (campo) => campo.value.replace(/ /g, ' ');

const display = new Campo('valor-display');
const hidden = new Campo('valor-hidden', '0.00');
const mascara = criarMascaraMoeda({ displayId: 'valor-display', hiddenId: 'valor-hidden' });

ok(visto(display) === 'R$ 0,00', `parte de zero (${visto(display)})`);

display.teclar('1');
ok(visto(display) === 'R$ 0,01', `digitar 1 -> R$ 0,01 (${visto(display)})`);

'2000'.split('').forEach(d => display.teclar(d));
ok(visto(display) === 'R$ 120,00', `depois 2000 -> R$ 120,00 (${visto(display)})`);
ok(mascara.valor() === '120.00', `valor() devolve decimal canônico (${mascara.valor()})`);
ok(hidden.value === '120.00', `o campo oculto acompanha (${hidden.value})`);

display.teclar('Backspace');
ok(visto(display) === 'R$ 12,00', `Backspace tira o último dígito (${visto(display)})`);

display.teclar('Delete');
ok(visto(display) === 'R$ 0,00', `Delete zera (${visto(display)})`);

ok(display.teclar('a') === false, 'letra não é barrada nem entra — o campo ignora');
ok(visto(display) === 'R$ 0,00', 'e o valor continua zerado depois da letra');
ok(display.teclar('Tab') === false, 'Tab passa pelo navegador (não bloqueia a navegação)');
ok(display.colar() === true, 'colar é bloqueado — a máscara não sabe ler texto pronto');

// milhar
'123456'.split('').forEach(d => display.teclar(d));
ok(visto(display) === 'R$ 1.234,56', `separador de milhar (${visto(display)})`);

// teto: R$ 999.999.999,99 — o 12º dígito não entra
mascara.definir(999999999.99);
ok(visto(display) === 'R$ 999.999.999,99', `definir() escreve no campo (${visto(display)})`);
display.teclar('9');
ok(visto(display) === 'R$ 999.999.999,99', 'no teto, um dígito a mais não muda nada');

// valor inicial vindo do servidor
const d2 = new Campo('v2-display');
new Campo('v2-hidden', '15000.00');
criarMascaraMoeda({ displayId: 'v2-display', hiddenId: 'v2-hidden' });
ok(visto(d2) === 'R$ 15.000,00', `valor do servidor aparece formatado (${visto(d2)})`);

// sem campo oculto, o valor inicial vem de `inicial`
const d3 = new Campo('v3-display');
const m3 = criarMascaraMoeda({ displayId: 'v3-display', inicial: '7.5' });
ok(visto(d3) === 'R$ 7,50', `sem hidden, usa config.inicial (${visto(d3)})`);
ok(m3.valor() === '7.50', `e valor() segue certo (${m3.valor()})`);

ok(criarMascaraMoeda({ displayId: 'nao-existe' }) === null,
   'campo ausente devolve null em vez de estourar');

console.log(falhas ? `\n${falhas} falha(s)` : '\ntudo passou');
process.exit(falhas ? 1 : 0);
