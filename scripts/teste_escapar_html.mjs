/**
 * Teste de comportamento do escape de HTML (static/js/escapar_html.js).
 *
 *     node scripts/teste_escapar_html.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(fileURLToPath(import.meta.url), '../..');
const src = fs.readFileSync(path.join(REPO, 'templates/static/js/escapar_html.js'), 'utf8');
const escaparHtml = new Function(`${src}\nreturn escaparHtml;`)();

const CASOS = [
    ['<img src=x onerror="a()">', '&lt;img src=x onerror=&quot;a()&quot;&gt;'],
    ["O'Brien & Filhos", 'O&#39;Brien &amp; Filhos'],
    ['" autofocus onfocus="a()', '&quot; autofocus onfocus=&quot;a()'],
    // entidade digitada pelo usuário continua aparecendo como foi digitada
    ['&amp;', '&amp;amp;'],
    ['João da Silva', 'João da Silva'],
    ['', ''],
    [null, ''],
    [undefined, ''],
    [0, '0'],
    [42, '42'],
];

let falhas = 0;
for (const [entrada, esperado] of CASOS) {
    const obtido = escaparHtml(entrada);
    const ok = obtido === esperado;
    if (!ok) falhas++;
    console.log(`[${ok ? ' ok ' : 'FALHA'}] ${JSON.stringify(entrada)} → ${JSON.stringify(obtido)}`);
}
console.log(falhas ? `\n${falhas} falha(s)` : '\ntudo passou');
process.exit(falhas ? 1 : 0);
