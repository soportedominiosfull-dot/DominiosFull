function inicializarMenu() {
    const btnMenu = document.getElementById('btnMenu');
    const navMenu = document.getElementById('navMenu');

    if (btnMenu && navMenu) {
        btnMenu.onclick = (e) => {
            e.stopPropagation();
            navMenu.classList.toggle('active');
        };
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarMenu);
} else {
    inicializarMenu();
}