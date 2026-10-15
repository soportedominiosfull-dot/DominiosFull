document.addEventListener('DOMContentLoaded', function () {
    const usuarioBtn = document.querySelector('.usuario-btn');
    const usuarioMenu = document.getElementById('usuarioMenu');

    if (usuarioBtn && usuarioMenu) {
        usuarioBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const visible = usuarioMenu.classList.toggle('show');
            usuarioBtn.setAttribute('aria-expanded', visible ? 'true' : 'false');
        });

        document.addEventListener('click', function (event) {
            if (!usuarioBtn.contains(event.target) && !usuarioMenu.contains(event.target)) {
                usuarioMenu.classList.remove('show');
                usuarioBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
});