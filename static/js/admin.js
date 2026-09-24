// Maneja la interacción para mostrar y ocultar la barra lateral de navegación
const botonMenu = document.getElementById('btnMenu');
const barraLateral = document.getElementById('sidebar');

if (botonMenu && barraLateral) {
    botonMenu.onclick = () => barraLateral.classList.toggle('active');
}