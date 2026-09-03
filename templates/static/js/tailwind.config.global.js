/**
 * Tema do SIMU-PROJUDI — valores do Guia de Design (IESGO, versão 1.0).
 *
 * Só entram aqui valores que existem no guia. Ao precisar de uma cor nova,
 * confira o guia antes de inventar: a regra é copiar, não criar variação.
 *
 * O vocabulário antigo do TJGO foi removido por completo:
 * de propósito — qualquer resquício deixa de pintar e aparece na revisão.
 */
tailwind.config = {
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

                /* ── Compatibilidade temporária ────────────────────────────
                   Os nomes antigos apontam para a paleta nova, para que as
                   telas ainda não convertidas exibam as cores do guia em vez
                   de ficarem sem cor nenhuma.
                   REMOVER quando a Fase 3 terminar — a guarda de classes
                   órfãs acusa qualquer uso remanescente. */
                'tjgo-navy':            '#0a083d',
                'tjgo-blue':            '#1f4f9c',
                'tjgo-light-blue':      '#1f4f9c',
                'tjgo-gray-bg':         '#f4f5f7',
                'tjgo-gray-card':       '#f1f2f4',
                'tjgo-gray-card-hover': '#eef0f3',
                'tjgo-gray-border':     '#e2e5ea',
                'tjgo-text-main':       '#23262e',
                'tjgo-text-light':      '#6b7280',
                'azul-marinho':         '#0a083d',
                'azul-primario':        '#1f4f9c',
                'azul-botao':           '#0a083d',
                'fundo-geral':          '#f4f5f7',
                'fundo-container':      '#ffffff',
                'fundo-caixa':          '#fbfbfc',
                'hover-caixa':          '#eef0f3',
                'texto-principal':      '#23262e',
                'texto-secundario':     '#6b7280',
                'borda':                '#e2e5ea',
            },

            fontFamily: {
                sans: ['Barlow', 'Helvetica', 'Arial', 'sans-serif'],
                mono: ['IBM Plex Mono', 'ui-monospace', 'Consolas', 'monospace'],
            },

            /* Escala tipográfica do guia (seção 03) */
            fontSize: {
                'micro':  ['10px',   { letterSpacing: '.1em' }],  // menor tamanho que o guia admite
                'meta':   ['10.5px', { lineHeight: '1.5' }],
                'apoio':  ['11px',   { lineHeight: '1.6' }],
                'dado':   ['11.5px', { lineHeight: '1.6' }],
                'corpo':  ['12px',   { lineHeight: '1.6' }],
                'h1':     ['26px',   { lineHeight: '1.15', letterSpacing: '-0.01em' }],
                'kpi':    ['28px',   { lineHeight: '1' }],
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
