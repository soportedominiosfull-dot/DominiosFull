document.addEventListener('DOMContentLoaded', () => {
    // 1. Carrusel horizontal de opiniones
    const trackOpiniones = document.getElementById('opinionesTrack');
    let posicionCarrusel = 0;

    function moverCarruselOpiniones() {
        if (!trackOpiniones || trackOpiniones.children.length <= 1) return;

        posicionCarrusel++;
        if (posicionCarrusel >= trackOpiniones.children.length) {
            posicionCarrusel = 0;
        }

        const anchoTarjeta = trackOpiniones.children[0].offsetWidth + 20;
        trackOpiniones.style.transform = `translateX(-${posicionCarrusel * anchoTarjeta}px)`;
    }

    if (trackOpiniones) {
        setInterval(moverCarruselOpiniones, 4000);
    }

    // 2. Control del modal y filtros de opiniones
    const modalFiltro = document.getElementById('filtroOpiniones');
    const btnAbrirModal = document.getElementById('btnAbrirFiltro');
    const btnCerrarModal = document.getElementById('btnCerrarFiltro');
    const botonesFiltro = document.querySelectorAll('.btn-filtro');
    const itemsOpiniones = document.querySelectorAll('.item-opinion-filtro');

    // Abrir modal
    if (btnAbrirModal && modalFiltro) {
        btnAbrirModal.addEventListener('click', () => {
            modalFiltro.classList.add('active');
        });
    }

    // Cerrar modal
    if (btnCerrarModal && modalFiltro) {
        btnCerrarModal.addEventListener('click', () => {
            modalFiltro.classList.remove('active');
        });
    }

    // Cierre al hacer clic fuera del contenido del modal
    window.addEventListener('click', (event) => {
        if (event.target === modalFiltro) {
            modalFiltro.classList.remove('active');
        }
    });

    // Filtrado dinámico por estrellas
    botonesFiltro.forEach(boton => {
        boton.addEventListener('click', () => {
            const estrellas = boton.getAttribute('data-filtro');

            // Cambia el estado activo visual
            botonesFiltro.forEach(b => b.classList.remove('active'));
            boton.classList.add('active');

            // Oculta/Muestra las opiniones según la selección
            itemsOpiniones.forEach(item => {
                if (estrellas === 'todas' || item.getAttribute('data-estrellas') === estrellas) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
});