document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll(".slide");
    const btnAnt = document.getElementById("btnSlideAnt");
    const btnSig = document.getElementById("btnSlideSig");
    let index = 0;
    let modoVozActivado = false;

    // Reproduce texto mediante síntesis de voz
    function decir(texto) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(texto);
        msg.lang = 'es-ES';
        window.speechSynthesis.speak(msg);
    }

    // Gestiona la visualización del slide activo
    function mostrar(i) {
        slides.forEach((slide, idx) => {
            const v = slide.querySelector("video");
            
            if (idx === i) {
                slide.classList.add("activo");
                if (v) {
                    v.muted = true; // Requisito estricto de iOS
                    const playPromise = v.play();
                    if (playPromise !== undefined) {
                        playPromise.catch(() => {
                            // Ignora bloqueos por ahorro de batería en móviles
                        });
                    }
                }
            } else {
                slide.classList.remove("activo");
                if (v) {
                    v.pause();
                    v.currentTime = 0;
                }
            }
        });
    }

    function siguiente() {
        index = (index + 1) % slides.length;
        mostrar(index);
    }

    function anterior() {
        index = (index - 1 + slides.length) % slides.length;
        mostrar(index);
    }

    // Asignación de eventos a los botones de navegación
    if (btnSig) btnSig.addEventListener("click", siguiente);
    if (btnAnt) btnAnt.addEventListener("click", anterior);

    // Avanzar de slide al terminar la reproducción
    document.querySelectorAll(".slide video").forEach(v => {
        v.addEventListener("ended", siguiente);
    });

    // Inicializador con confirmación de TalkBack
    function iniciarWeb(activarVoz) {
        modoVozActivado = activarVoz;
        mostrar(0);
    }

    // Modal de confirmación inicial
    setTimeout(() => {
        const confirmacion = confirm("Bienvenido a DominiosFull. ¿Deseas activar la función de voz (TalkBack)?");
        iniciarWeb(confirmacion);

        if (confirmacion) {
            setTimeout(() => {
                decir("Modo de voz activado. Bienvenido a DominiosFull, utilice el botón tabulador para navegar.");
            }, 500);

            if (!window.__dominiosfull_talkback_installed) {
                document.addEventListener('mousedown', (e) => {
                    const elemento = e.target.closest('a, button, h1, h2, h3, p');
                    if (elemento) {
                        const textoParaLeer = elemento.getAttribute('aria-label') || elemento.innerText;
                        if (textoParaLeer) setTimeout(() => decir(textoParaLeer), 50);
                    }
                });

                document.addEventListener('focus', (e) => {
                    const elemento = e.target;
                    if (elemento && typeof elemento.matches === 'function') {
                        if (elemento.matches('a, button')) {
                            const textoParaLeer = elemento.getAttribute('aria-label') || elemento.innerText;
                            if (textoParaLeer) setTimeout(() => decir(textoParaLeer), 100);
                        }
                    }
                }, true);

                window.__dominiosfull_talkback_installed = true;
            }
        }
    }, 100);
});