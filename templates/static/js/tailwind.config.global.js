/**
 * Tema do SIMU-PROJUDI — valores do Guia de Design (IESGO, versão 1.0).
 *
 * Só entram aqui valores que existem no guia. Ao precisar de uma cor nova,
 * confira o guia antes de inventar: a regra é copiar, não criar variação.
 *
 * O vocabulário antigo do TJGO foi removido por completo:
 * de propósito — qualquer resquício deixa de pintar e aparece na revisão.
 */
tailwind.config = (function () {

/* Acessibilidade: A+/A- do cabeçalho não reescrevem classe nenhuma — só mudam
   `--escala-fonte` no <html> (ver static/js/acessibilidade.js). Por isso todo
   tamanho do guia sai daqui embrulhado em calc(): um valor só reescala a
   interface inteira, e o número do guia continua legível no fonte. */
const escalavel = (tamanho) => 'calc(' + tamanho + ' * var(--escala-fonte, 1))';

return {
    theme: {
        extend: {
            colors: {
                /* Marca */
                'navy':      '#0a083d',  // cabeçalho, títulos, botão primário
                'acao':      '#1f4f9c',  // links, aba ativa, foco de campo
                'marca':     '#d30000',  // fio de assinatura — nunca botão nem link
                'navy-40':   '#a7abcd',  // texto secundário sobre navy

                /* Neutros de interface */
                'pagina':       '#f4f5f7',
                'card-topo':    '#fbfbfc',
                'tabela-topo':  '#f7f8fa',
                'contorno':     '#e2e5ea',
                'divisor':      '#eef0f3',
                'campo-borda':  '#d3d7de',
                'texto':        '#23262e',
                'texto-neutro': '#4b5563',
                'rotulo':       '#6b7280',
                'linha-hover':  '#f7faff',

                /* Estados — cada um é um trio fundo / texto / borda */
                'ok-bg':      '#eaf4ec', 'ok-txt':      '#2e7d32', 'ok-bd':      '#bee0c2',
                'atencao-bg': '#fff5e4', 'atencao-txt': '#a96400', 'atencao-bd': '#f1d59c',
                'erro-bg':    '#fdeeee', 'erro-txt':    '#b33a3a', 'erro-bd':    '#f3cfcf',
                'neutro-bg':  '#f1f2f4', 'neutro-txt':  '#5b6270', 'neutro-bd':  '#d8dbe1',
                'validacao':  '#c0392b',  // erro de validação de campo
                'desabilitado': '#9ca3af',  // texto de botão desabilitado (guia seção 04)

            },

            fontFamily: {
                sans: ['Barlow', 'Helvetica', 'Arial', 'sans-serif'],
                mono: ['Lato', 'Helvetica', 'Arial', 'sans-serif'],
            },

            /* Escala tipográfica do guia (seção 03) */
            fontSize: {
                'micro':  [escalavel('10px'),   { letterSpacing: '.1em' }],  // menor tamanho que o guia admite
                'meta':   [escalavel('10.5px'), { lineHeight: '1.5' }],
                'apoio':  [escalavel('11px'),   { lineHeight: '1.6' }],
                'dado':   [escalavel('11.5px'), { lineHeight: '1.6' }],
                'corpo':  [escalavel('12px'),   { lineHeight: '1.6' }],
                'h1':     [escalavel('26px'),   { lineHeight: '1.15', letterSpacing: '-0.01em' }],
                'kpi':    [escalavel('28px'),   { lineHeight: '1' }],

                /* Fora do guia — mas escritos em telas que existem, e o
                   verificar.py continua avisando sobre eles. Reescritos aqui
                   com os mesmos valores do Tailwind só para que o A+/A- não
                   deixe um punhado de rótulos parados enquanto o resto cresce. */
                'xs':   [escalavel('0.75rem'),  { lineHeight: '1rem' }],
                'sm':   [escalavel('0.875rem'), { lineHeight: '1.25rem' }],
                'base': [escalavel('1rem'),     { lineHeight: '1.5rem' }],
                'lg':   [escalavel('1.125rem'), { lineHeight: '1.75rem' }],
                'xl':   [escalavel('1.25rem'),  { lineHeight: '1.75rem' }],
                '2xl':  [escalavel('1.5rem'),   { lineHeight: '2rem' }],
                '3xl':  [escalavel('1.875rem'), { lineHeight: '2.25rem' }],
            },

            maxWidth: {
                'conteudo': '1280px',
            },

            zIndex: {
                'cabecalho': '40',
                'navegacao': '30',
                'modal':     '60',
                'toast':     '70',
            },
        },

        /* Sobrescreve a escala inteira — não estende.
           Com isso, todo `rounded*` já escrito nos templates resolve para 0 e
           todo `shadow*` para none, sem precisar editar tela por tela. */
        borderRadius: {
            'none':   '0',
            DEFAULT:  '0',
            'sm':     '0',
            'md':     '0',
            'lg':     '0',
            'xl':     '0',
            '2xl':    '0',
            '3xl':    '0',
            'campo':  '2px',    // única exceção: campo de formulário
            'full':   '9999px', // avatar e ponto de status
        },

        boxShadow: {
            'none':  'none',
            DEFAULT: 'none',
            'sm':    'none',
            'md':    'none',
            'lg':    'none',
            'xl':    'none',
            '2xl':   'none',
            'inner': 'none',
            'modal': '0 24px 60px -12px rgba(10,8,61,.45)',
        },
    }
}

})();
