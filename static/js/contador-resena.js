document.addEventListener('DOMContentLoaded', function () {
    const textarea = document.getElementById('comentario');
    const contador = document.getElementById('contadorChar');

    if (textarea && contador) {
        const actualizarContador = () => {
            const actual = textarea.value.length;
            const maximo = textarea.getAttribute('maxlength') || '86';
            contador.textContent = `${actual}/${maximo}`;
        };

        textarea.addEventListener('input', actualizarContador);
        textarea.addEventListener('keyup', actualizarContador);

        actualizarContador();
    }
});