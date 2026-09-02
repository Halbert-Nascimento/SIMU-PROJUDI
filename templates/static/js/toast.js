/**
 * Notificação flutuante de canto — usada por pagina_aluno, avaliar e
 * movimentar_processo. O markup vem de base/components/_toast.html.
 *
 *   showToast("Movimentação registrada");
 *   showToast("Arquivo excedeu o limite", true);
 */
function showToast(msg, err, duracaoMs) {
    var t = document.getElementById("toast");
    var alvo = document.getElementById("toastMsg");
    if (!t || !alvo) return;

    alvo.textContent = msg;
    t.style.background = err ? "#c0392b" : "#2e7d32";
    t.classList.add("show");

    // cada chamada reinicia a contagem — toasts em sequência não se cortam
    clearTimeout(t._toastTimer);
    t._toastTimer = setTimeout(function () {
        t.classList.remove("show");
    }, duracaoMs || 2600);
}
