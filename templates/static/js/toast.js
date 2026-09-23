/**
 * Notificação flutuante no centro superior. Cada aviso é montado aqui e
 * empilhado em #toast-pilha — o markup da pilha vem de
 * base/components/_toast.html, e é criado sob demanda quando a tela não
 * incluiu o componente.
 *
 *   showToast("Movimentação registrada nos autos.", "sucesso");
 *   showToast("Arquivo excedeu o limite de 7 MB.", "erro");
 *
 * Tipos: "sucesso" | "atencao" | "erro" | "info". A assinatura antiga
 * showToast(msg, true) continua valendo e cai em "erro".
 */
var TOAST_ESTADOS = {
    sucesso: { rotulo: 'Sucesso',    icone: 'fa-circle-check',         duracao: 2600 },
    atencao: { rotulo: 'Atenção',    icone: 'fa-triangle-exclamation', duracao: 4500 },
    erro:    { rotulo: 'Erro',       icone: 'fa-circle-xmark',         duracao: 6000 },
    info:    { rotulo: 'Informação', icone: 'fa-circle-info',          duracao: 2600 },
};

var TOAST_MAX_VISIVEIS = 3;
var TOAST_SAIDA_MS = 200;

function showToast(msg, tipo, duracaoMs) {
    var chave = normalizarTipoToast(tipo);
    var estado = TOAST_ESTADOS[chave];
    var duracao = duracaoMs || estado.duracao;
    var pilha = obterPilhaToast();

    // erro interrompe a leitura em curso; o resto espera a pausa do leitor de tela
    pilha.setAttribute('aria-live', chave === 'erro' ? 'assertive' : 'polite');

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + chave;

    var linha = document.createElement('div');
    linha.className = 'toast__linha';

    var icone = document.createElement('span');
    icone.className = 'toast__icone';
    var glifo = document.createElement('i');
    glifo.className = 'fa-solid ' + estado.icone;
    glifo.setAttribute('aria-hidden', 'true');
    icone.appendChild(glifo);

    var corpo = document.createElement('div');
    corpo.className = 'toast__corpo';
    var rotulo = document.createElement('span');
    rotulo.className = 'toast__rotulo';
    rotulo.textContent = estado.rotulo;
    var texto = document.createElement('span');
    texto.className = 'toast__texto';
    texto.textContent = msg;
    corpo.appendChild(rotulo);
    corpo.appendChild(texto);

    var fechar = document.createElement('button');
    fechar.type = 'button';
    fechar.className = 'toast__fechar';
    fechar.setAttribute('aria-label', 'Fechar aviso');
    var xis = document.createElement('i');
    xis.className = 'fa-solid fa-xmark';
    xis.setAttribute('aria-hidden', 'true');
    fechar.appendChild(xis);
    fechar.addEventListener('click', function () { removerToast(toast); });

    linha.appendChild(icone);
    linha.appendChild(corpo);
    linha.appendChild(fechar);

    var tempo = document.createElement('div');
    tempo.className = 'toast__tempo';
    var barra = document.createElement('span');
    barra.style.animationDuration = duracao + 'ms';
    tempo.appendChild(barra);

    toast.appendChild(linha);
    toast.appendChild(tempo);

    pilha.insertBefore(toast, pilha.firstChild);

    // reflow antes do .show: sem ele o navegador funde os dois estados e a entrada não roda
    void toast.offsetWidth;
    toast.classList.add('show');

    while (pilha.children.length > TOAST_MAX_VISIVEIS) {
        removerToast(pilha.lastElementChild);
    }

    toast._toastTimer = setTimeout(function () { removerToast(toast); }, duracao);
}

function normalizarTipoToast(tipo) {
    if (tipo === true) return 'erro';
    if (!tipo || !Object.prototype.hasOwnProperty.call(TOAST_ESTADOS, tipo)) return 'info';
    return tipo;
}

function obterPilhaToast() {
    var pilha = document.getElementById('toast-pilha');
    if (!pilha) {
        pilha = document.createElement('div');
        pilha.id = 'toast-pilha';
        pilha.className = 'toast-pilha';
        pilha.setAttribute('aria-atomic', 'false');
        document.body.appendChild(pilha);
    }
    return pilha;
}

function removerToast(toast) {
    if (!toast || toast._toastSaindo) return;
    toast._toastSaindo = true;
    clearTimeout(toast._toastTimer);
    toast.classList.remove('show');
    setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, TOAST_SAIDA_MS);
}
