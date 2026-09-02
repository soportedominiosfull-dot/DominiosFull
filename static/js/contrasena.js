(function () {
    // Clave donde talkback.js guarda si esta activado o desactivado
    const ENABLED_KEY = 'dominiosfull_talkback_enabled';

    function estaTalkbackActivado() {
        return localStorage.getItem(ENABLED_KEY) === 'true';
    }

    function hablarDirecto(texto) {
        // Ejecuta la sintesis de voz solo si la funcion esta activa en localStorage
        if (!estaTalkbackActivado()) {
            return;
        }

        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(texto);
            utterance.lang = 'es-ES';
            window.speechSynthesis.speak(utterance);
        }
    }

    function inicializarMonitos() {
        // Busca todos los botones de conmutacion de contrasena
        const botonesMonito = document.querySelectorAll('.toggle-password, #btn-monito');

        if (botonesMonito.length === 0) {
            return;
        }

        // Asigna eventos de visibilidad a cada boton encontrado
        botonesMonito.forEach(btnMonito => {
            const contenedor = btnMonito.closest('.password-container, .password-group');
            const inputPassword = contenedor 
                ? contenedor.querySelector('input') 
                : btnMonito.previousElementSibling;

            if (!inputPassword) return;

            function alternarPassword(e) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }

                const esPassword = inputPassword.type === 'password';

                if (esPassword) {
                    inputPassword.type = 'text';
                    btnMonito.textContent = '🙉';
                    hablarDirecto('Contraseña visible');
                } else {
                    inputPassword.type = 'password';
                    btnMonito.textContent = '🙈';
                    hablarDirecto('Contraseña oculta');
                }
            }

            // Asignacion de eventos por clic y teclado
            btnMonito.addEventListener('click', alternarPassword);

            btnMonito.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    alternarPassword(e);
                }
            });
        });
    }

    function inicializarValidacionRegistro() {
        const form = document.querySelector(".iniciar-sesion form");
        const password = document.getElementById("password");
        const confirmar = document.getElementById("confirmar");
        const error = document.getElementById("error-password");

        if (!form || !password || !confirmar || !error) return;

        // Valida que los campos de contrasena coincidan antes de enviar
        form.addEventListener("submit", function(e) {
            if (password.value !== confirmar.value) {
                e.preventDefault(); 
                error.textContent = "Las contraseñas no coinciden";
                hablarDirecto(error.textContent); 
            } else {
                error.textContent = "";
            }
        });
    }

    function inicializarScript() {
        inicializarMonitos();
        inicializarValidacionRegistro();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarScript);
    } else {
        inicializarScript();
    }
})();