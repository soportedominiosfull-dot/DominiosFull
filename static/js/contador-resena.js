document.addEventListener('DOMContentLoaded', () => {
    const inputComentario = document.getElementById('comentario');
    const contador = document.getElementById('contadorChar');

    if (inputComentario && contador) {
        inputComentario.addEventListener('input', () => {
            contador.textContent = `${inputComentario.value.length}/86`;
        });
    }
});