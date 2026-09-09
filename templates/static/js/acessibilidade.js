/**
 * Ajuste de fonte do cabeçalho (A+ / A-).
 *
 * A única coisa que este arquivo escreve é `--escala-fonte` no <html>. Quem
 * converte isso em tamanho é o tema (`tailwind.config.global.js`) e as folhas
 * de estilo, onde todo px de texto está embrulhado em `calc()`. Nenhuma classe
 * é trocada e nenhum tamanho é decidido aqui — do contrário a escala do guia
 * passaria a ter dois donos.
 *
 * Carregado no <head>, antes da primeira pintura, para que a preferência
 * guardada não apareça como um salto de tamanho depois da tela montada.
 */
(function () {
    'use strict';

    var ESCALAS = [0.9, 1, 1.1, 1.2, 1.3, 1.4];
    var PADRAO  = 1;
    var CHAVE   = 'simu:escala-fonte';

    function indiceGuardado() {
        try {
            var i = ESCALAS.indexOf(parseFloat(localStorage.getItem(CHAVE)));
            return i === -1 ? ESCALAS.indexOf(PADRAO) : i;
        } catch (e) {
            return ESCALAS.indexOf(PADRAO);  // navegador com armazenamento bloqueado
        }
    }

    var indice = indiceGuardado();
    var aviso  = null;

    function aplicar() {
        document.documentElement.style.setProperty('--escala-fonte', ESCALAS[indice]);
    }

    aplicar();

    function percentual() {
        return Math.round(ESCALAS[indice] * 100) + '%';
    }

    function guardar() {
        try {
            localStorage.setItem(CHAVE, ESCALAS[indice]);
        } catch (e) { /* sem armazenamento: vale só para esta navegação */ }
    }

    function sincronizarBotoes(botoes) {
        botoes.forEach(function (botao) {
            var passo = parseInt(botao.dataset.escalaFonte, 10);
            var alvo  = indice + passo;
            botao.disabled = alvo < 0 || alvo >= ESCALAS.length;
            botao.title = (passo > 0 ? 'Aumentar fonte' : 'Diminuir fonte')
                        + ' (atual: ' + percentual() + ')';
        });
    }

    // Sem isto, quem usa leitor de tela pressiona o botão e não recebe retorno
    // nenhum: o tamanho muda, mas nada no documento anuncia que mudou.
    function anunciar() {
        if (!aviso) {
            aviso = document.createElement('span');
            aviso.setAttribute('role', 'status');
            aviso.setAttribute('aria-live', 'polite');
            aviso.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;'
                                + 'clip:rect(0 0 0 0);white-space:nowrap;';
            document.body.appendChild(aviso);
        }
        aviso.textContent = 'Tamanho da fonte em ' + percentual() + '.';
    }

    document.addEventListener('DOMContentLoaded', function () {
        var botoes = Array.prototype.slice.call(
            document.querySelectorAll('[data-escala-fonte]'));
        if (!botoes.length) return;

        botoes.forEach(function (botao) {
            botao.addEventListener('click', function () {
                var alvo = indice + parseInt(botao.dataset.escalaFonte, 10);
                if (alvo < 0 || alvo >= ESCALAS.length) return;
                indice = alvo;
                aplicar();
                guardar();
                sincronizarBotoes(botoes);
                anunciar();
            });
        });

        sincronizarBotoes(botoes);
    });
})();
