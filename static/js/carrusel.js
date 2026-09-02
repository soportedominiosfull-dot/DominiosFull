// Gestiona la funcionalidad del carrusel de videos y la síntesis de voz en la página de inicio
let slides = document.querySelectorAll(".slide");
let index = 0;
let modoVozActivado = false;

// Reproduce texto mediante síntesis de voz
function decir(texto) {
    window.speechSynthesis.cancel();
    const msg = new SpeechSynthesisUtterance(texto);
    msg.lang = 'es-ES';
    window.speechSynthesis.speak(msg);
}

// Inicializa el carrusel y la configuración de voz según la respuesta del usuario
function iniciarWeb(activarVoz) {
    modoVozActivado = activarVoz;
    mostrar(0);
}

// Solicita la confirmación de la función de voz al cargar la página
window.onload = () => {
    let confirmacion = confirm("Bienvenido a DominiosFull. ¿Deseas activar la función de voz (TalkBack)?");
    
    iniciarWeb(confirmacion);
    
    if (confirmacion) {
        setTimeout(() => {
            decir("Modo de voz activado. Bienvenido a DominiosFull, utilice el boton tabulador para navegar.");
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
};

// Escucha los eventos para avanzar al siguiente slide cuando finaliza cada video
document.querySelectorAll(".slide video").forEach(v => {
    v.addEventListener("ended", function() {
        siguiente();
    });
});

// Gestiona la visualización del slide activo y el estado de reproducción de los videos
function mostrar(i) {
    slides.forEach((slide, idx) => {
        let v = slide.querySelector("video");
        
        if (idx === i) {
            slide.classList.add("activo");
            if (v) v.play().catch(() => {});
        } else {
            slide.classList.remove("activo");
            if (v) {
                v.pause();
                v.currentTime = 0;
            }
        }
    });
}

// Incrementa el índice para avanzar al siguiente slide
function siguiente() {
    index++;
    if (index >= slides.length) {
        index = 0;
    }
    mostrar(index);
}

// Decrementa el índice para regresar al slide anterior
function anterior() {
    index--;
    if (index < 0) {
        index = slides.length - 1;
    }
    mostrar(index);
}