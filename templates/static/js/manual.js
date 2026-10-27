(function () {
    'use strict';

    var menu = document.querySelector('[data-menu-manual]');
    if (menu && window.matchMedia('(max-width: 1023px)').matches) menu.open = false;

    // Busca local: o índice é um JSON estático, carregado só quando alguém usa o campo.
    var campo = document.getElementById('manual-busca-campo');
    var lista = document.getElementById('manual-busca-resultados');
    var indice = null;
    var carregando = false;

    function semAcento(texto) {
        return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }

    function titulosDosCapitulos() {
        var titulos = {};
        document.querySelectorAll('.manual-capitulos a[data-slug]').forEach(function (a) {
            titulos[a.dataset.slug] = a.textContent.trim();
        });
        return titulos;
    }

    function carregarIndice() {
        if (indice || carregando || !campo) return;
        carregando = true;
        fetch(campo.dataset.buscaUrl)
            .then(function (r) { return r.json(); })
            .then(function (dados) {
                indice = dados.map(function (e) {
                    return { c: e.c, i: e.i, h: e.h, hn: semAcento(e.h), xn: semAcento(e.x) };
                });
                buscar();
            })
            .catch(function () { carregando = false; });
    }

    function pontuar(entrada, termos) {
        var pontos = 0;
        for (var i = 0; i < termos.length; i++) {
            var noTitulo = entrada.hn.indexOf(termos[i]) !== -1;
            var noTexto = entrada.xn.indexOf(termos[i]) !== -1;
            if (!noTitulo && !noTexto) return 0;
            pontos += noTitulo ? 3 : 1;
        }
        return pontos;
    }

    function limpar() {
        lista.hidden = true;
        lista.replaceChildren();
    }

    function buscar() {
        if (!indice) return;
        var termos = semAcento(campo.value).split(/\s+/).filter(function (t) { return t.length > 1; });
        if (!termos.length) { limpar(); return; }

        var titulos = titulosDosCapitulos();
        var achados = indice
            .map(function (e) { return { e: e, p: pontuar(e, termos) }; })
            .filter(function (r) { return r.p > 0; })
            .sort(function (a, b) { return b.p - a.p; })
            .slice(0, 8);

        lista.replaceChildren();
        if (!achados.length) {
            var vazio = document.createElement('li');
            vazio.className = 'manual-busca-vazio';
            vazio.textContent = 'Nada encontrado para essa busca.';
            lista.appendChild(vazio);
        }
        achados.forEach(function (r) {
            var item = document.createElement('li');
            var link = document.createElement('a');
            link.href = campo.dataset.capituloBase + r.e.c + '/#' + r.e.i;
            var titulo = document.createElement('span');
            titulo.className = 'manual-busca-resultado-titulo';
            titulo.textContent = r.e.h;
            var capitulo = document.createElement('span');
            capitulo.className = 'manual-busca-resultado-capitulo';
            capitulo.textContent = titulos[r.e.c] || r.e.c;
            link.append(titulo, capitulo);
            item.appendChild(link);
            lista.appendChild(item);
        });
        lista.hidden = false;
    }

    if (campo && lista) {
        campo.addEventListener('focus', carregarIndice);
        campo.addEventListener('input', function () { carregarIndice(); buscar(); });
        campo.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { campo.value = ''; limpar(); }
        });
    }

    // Filtro por papel da linha do processo; sem JavaScript a lista inteira continua visível.
    var filtro = document.querySelector('[data-filtro-papeis]');
    if (filtro) {
        filtro.hidden = false;
        filtro.addEventListener('click', function (e) {
            var botao = e.target.closest('[data-filtro-papel]');
            if (!botao) return;
            var papel = botao.dataset.filtroPapel;
            filtro.querySelectorAll('.tab').forEach(function (aba) {
                aba.classList.toggle('active', aba === botao);
            });
            document.querySelectorAll('[data-fase]').forEach(function (fase) {
                var visiveis = 0;
                fase.querySelectorAll('tbody tr').forEach(function (linha) {
                    var papeis = (linha.dataset.papeis || '').split(' ');
                    var mostrar = !papel || papeis.indexOf(papel) !== -1;
                    linha.hidden = !mostrar;
                    if (mostrar) visiveis++;
                });
                fase.hidden = visiveis === 0;
            });
        });
    }

    // Ampliação das capturas; sem JavaScript o link abre a imagem em outra aba.
    var ampliada = null;
    document.addEventListener('click', function (e) {
        var link = e.target.closest('a[data-ampliar]');
        if (!link || typeof HTMLDialogElement === 'undefined') return;
        e.preventDefault();
        if (!ampliada) {
            ampliada = document.createElement('dialog');
            ampliada.className = 'manual-ampliada';
            var fechar = document.createElement('button');
            fechar.type = 'button';
            fechar.textContent = 'Fechar';
            var imagem = document.createElement('img');
            imagem.alt = '';
            ampliada.append(fechar, imagem);
            ampliada.addEventListener('click', function (ev) {
                if (ev.target !== imagem) ampliada.close();
            });
            document.body.appendChild(ampliada);
        }
        ampliada.querySelector('img').src = link.href;
        ampliada.showModal();
    });
})();
