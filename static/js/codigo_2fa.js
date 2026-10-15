document.addEventListener('DOMContentLoaded', function() {
    const inputCodigo = document.getElementById('codigo');

    if (inputCodigo) {
        // Pone el foco directamente para que TalkBack lo detecte e identifique de inmediato
        inputCodigo.focus();

        // Limpia cualquier caracter que no sea un número en tiempo real
        inputCodigo.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
});