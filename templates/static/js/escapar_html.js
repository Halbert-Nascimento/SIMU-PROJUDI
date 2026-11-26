/* Escapa um dado antes de interpolá-lo em HTML; serve a texto e a atributo entre aspas. */
function escaparHtml(valor) {
    const entidades = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(valor ?? '').replace(/[&<>"']/g, c => entidades[c]);
}
