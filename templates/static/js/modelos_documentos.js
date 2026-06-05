/**
 * Índice de modelos de documentos disponíveis no editor on-line.
 *
 * Para adicionar um novo modelo:
 *   1. Crie o arquivo HTML em:  templates/static/modelos/<slug>.html
 *   2. Adicione uma entrada no array MODELOS_INDEX abaixo.
 *   Nada mais precisa ser alterado.
 */

const MODELOS_INDEX = [
    {
        slug:  'peticao_inicial',
        label: 'Petição Inicial — Processo Civil Comum',
    },
    // Adicione novos modelos aqui:
    // { slug: 'contestacao', label: 'Contestação' },
    // { slug: 'recurso_apelacao', label: 'Recurso de Apelação' },
];

// ── Popula o <select> automaticamente ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const sel = document.getElementById('modeloSelect');
    if (!sel) return;

    MODELOS_INDEX.forEach(function (m) {
        const opt = document.createElement('option');
        opt.value = m.slug;
        opt.textContent = m.label;
        sel.appendChild(opt);
    });
});

// ── Carrega o HTML do modelo via fetch e injeta no TinyMCE ──────────────────
function carregarModelo() {
    const sel = document.getElementById('modeloSelect');
    const slug = sel.value;

    if (!slug) {
        showToast('Selecione um modelo antes de carregar', true);
        return;
    }

    const ed = tinymce.get('tinymce-editor');
    if (!ed) {
        showToast('Editor ainda carregando, aguarde...', true);
        return;
    }

    const url = STATIC_URL + 'modelos/' + slug + '.html';

    fetch(url)
        .then(function (res) {
            if (!res.ok) throw new Error('Modelo não encontrado (' + res.status + ')');
            return res.text();
        })
        .then(function (html) {
            ed.setContent(html);
            const label = sel.selectedOptions[0].text;
            document.getElementById('editorFileName').value = slug;
            showToast('Modelo carregado — edite os campos em destaque');
        })
        .catch(function (err) {
            showToast('Erro ao carregar modelo: ' + err.message, true);
        });
}
