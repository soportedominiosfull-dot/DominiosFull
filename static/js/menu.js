function inicializarMenu() {
    const btnMenu = document.getElementById('btnMenu');
    const navMenu = document.getElementById('navMenu');

    if (btnMenu && navMenu) {
        btnMenu.onclick = (e) => {
            e.stopPropagation();
            navMenu.classList.toggle('active');

            // Si se abre el menú, la pantalla se desplaza suavemente la página hacia arriba
            if (navMenu.classList.contains('active')) {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarMenu);
} else {
    inicializarMenu();
}