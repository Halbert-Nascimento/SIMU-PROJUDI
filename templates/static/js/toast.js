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
    // o fio de assinatura muda de cor no erro; o fundo continua navy
    t.classList.toggle("toast--erro", Boolean(err));
    t.classList.add("show");

    // cada chamada reinicia a contagem — toasts em sequência não se cortam
    clearTimeout(t._toastTimer);
    t._toastTimer = setTimeout(function () {
        t.classList.remove("show");
    }, duracaoMs || 2600);
}
