tailwind.config = {
    theme: {
        extend: {
            colors: {
                /* Paleta principal do sistema (tjgo-*) */
                'tjgo-navy':            '#153a61',
                'tjgo-blue':            '#1a5b9e',
                'tjgo-light-blue':      '#226bb8',
                'tjgo-gray-bg':         '#f4f4f4',
                'tjgo-gray-card':       '#e9e9e9',
                'tjgo-gray-card-hover': '#dedede',
                'tjgo-gray-border':     '#d1d1d1',
                'tjgo-text-main':       '#333333',
                'tjgo-text-light':      '#666666',
                /* Paleta dos formulários processuais (azul-*) */
                'azul-marinho':         '#153A61',
                'azul-primario':        '#1A5B9E',
                'azul-botao':           '#1E5894',
                'fundo-geral':          '#F7F7F7',
                'fundo-container':      '#FFFFFF',
                'fundo-caixa':          '#E9E9E9',
                'hover-caixa':          '#DCDCDC',
                'texto-principal':      '#333333',
                'texto-secundario':     '#666666',
                'borda':                '#D1D1D1',
            },
            fontFamily: {
                sans:     ['Arial', 'Helvetica', 'sans-serif'],
                'sistema':['Arial', 'Helvetica', 'sans-serif'],
            },
            maxWidth: {
                'container': '1200px',
            },
            boxShadow: {
                'card':  '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
                'modal': '0 10px 25px -5px rgba(0,0,0,0.3), 0 8px 10px -6px rgba(0,0,0,0.1)',
            },
        }
    }
}
