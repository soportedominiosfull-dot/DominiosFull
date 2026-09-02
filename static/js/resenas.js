// Animación del carrusel horizontal automático
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

// Intervalo para desplazar las tarjetas cada cuatro segundos
setInterval(moverCarruselOpiniones, 4000);

// Funciones para el control de la ventana filtro
function abrirFiltroOpiniones() {
    const modal = document.getElementById('filtroOpiniones'); // Corregido: 'f' minúscula
    if (modal) {
        modal.classList.add('active');
    }
}

function cerrarFiltroOpiniones() {
    const modal = document.getElementById('filtroOpiniones'); // Corregido: 'f' minúscula
    if (modal) {
        modal.classList.remove('active');
    }
}

// Filtrado dinámico de opiniones por estrellas
function filtrarOpiniones(estrellas, evento) {
    // Corregido: ahora selecciona .item-opinion-filtro que coincide con el HTML
    const items = document.querySelectorAll('.item-opinion-filtro'); 
    const botones = document.querySelectorAll('.btn-filtro');

    botones.forEach(btn => btn.classList.remove('active'));
    if (evento && evento.target) {
        evento.target.classList.add('active');
    }

    items.forEach(item => {
        if (estrellas === 'todas' || item.getAttribute('data-estrellas') === estrellas) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Cierre del filtro al interactuar fuera del contenido principal
window.addEventListener('click', function(event) {
    const modal = document.getElementById('filtroOpiniones'); // Corregido: 'f' minúscula
    if (event.target === modal) {
        cerrarFiltroOpiniones();
    }
});