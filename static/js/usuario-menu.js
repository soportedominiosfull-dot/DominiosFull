function toggleUsuarioMenu() {
    const menu = document.getElementById('usuarioMenu');
    if (!menu) {
        return;
    }
    menu.classList.toggle('show');
}

document.addEventListener('click', function (event) {
    const dropdown = document.querySelector('.usuario-dropdown');
    const menu = document.getElementById('usuarioMenu');
    if (!dropdown || !menu) {
        return;
    }

    if (!dropdown.contains(event.target)) {
        menu.classList.remove('show');
    }
});
