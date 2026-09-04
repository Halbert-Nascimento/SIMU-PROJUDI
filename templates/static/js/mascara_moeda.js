/**
 * Máscara monetária estilo caixa eletrônico: o dígito entra pelos centavos e
 * empurra o valor para a esquerda. Digitar `1` dá R$ 0,01; digitar `2000` em
 * seguida dá R$ 120,00. Não existe cursor no meio do número — é sempre a ponta.
 *
 *   const valorCausa = criarMascaraMoeda({
 *       displayId: "id_valor_causa_display",   // o campo que o usuário vê
 *       hiddenId:  "id_valor_causa",           // opcional: recebe "1234.56"
 *   });
 *   valorCausa.valor();        // "120.00" — decimal canônico, pronto para o POST
 *   valorCausa.definir(15.5);  // escreve R$ 15,50 no campo
 *
 * Sem `hiddenId`, o valor inicial vem de `config.inicial`.
 */
function formatarMoedaBR(valor) {
    return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function criarMascaraMoeda(config) {
    const display = document.getElementById(config.displayId);
    if (!display) return null;
    const hidden = config.hiddenId ? document.getElementById(config.hiddenId) : null;

    // centavos como inteiro: somar em float acumula erro de arredondamento
    const partida = hidden ? hidden.value : config.inicial;
    let centavos = Math.round(parseFloat(partida || "0") * 100);

    const TETO = 99999999999;   // R$ 999.999.999,99

    function atualizar() {
        display.value = formatarMoedaBR(centavos / 100);
        if (hidden) hidden.value = (centavos / 100).toFixed(2);
    }

    display.addEventListener("keydown", function (e) {
        if (e.key >= "0" && e.key <= "9") {
            e.preventDefault();
            if (centavos < TETO) {
                centavos = centavos * 10 + parseInt(e.key, 10);
                atualizar();
            }
        } else if (e.key === "Backspace") {
            e.preventDefault();
            centavos = Math.floor(centavos / 10);
            atualizar();
        } else if (e.key === "Delete") {
            e.preventDefault();
            centavos = 0;
            atualizar();
        }
        // Tab, setas e atalhos seguem o comportamento normal do navegador
    });

    // colar traria texto que a máscara não sabe interpretar
    display.addEventListener("paste", (e) => e.preventDefault());
    // reescreve por cima de qualquer entrada que escape do keydown
    display.addEventListener("input", () => {
        display.value = formatarMoedaBR(centavos / 100);
    });

    atualizar();   // aplica o valor que veio do servidor

    return {
        valor: () => (centavos / 100).toFixed(2),
        definir(reais) {
            centavos = Math.round((parseFloat(reais) || 0) * 100);
            atualizar();
        },
    };
}
