const GA_MEASUREMENT_ID = 'G-4CHMLP6638';

// Función para guardar una cookie en el navegador
function setCookie(nombre, valor, dias) {
    let fecha = new Date();
    fecha.setTime(fecha.getTime() + (dias * 24 * 60 * 60 * 1000));
    const expires = "expires=" + fecha.toUTCString();
    document.cookie = nombre + "=" + valor + ";" + expires + ";path=/;SameSite=Lax";
}

// Función para consultar si existe una cookie guardada
function getCookie(nombre) {
    const nombreEQ = nombre + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i].trim();
        if (c.indexOf(nombreEQ) === 0) return c.substring(nombreEQ.length, c.length);
    }
    return null;
}

document.addEventListener("DOMContentLoaded", function () {
    const banner = document.getElementById("cookie-banner");
    const btnAceptar = document.getElementById("accept-cookies");
    const btnRechazar = document.getElementById("reject-cookies");

    const consentimiento = getCookie("cookie_consent");

    if (!consentimiento) {
        if (banner) banner.style.display = "block";
    } else if (consentimiento === "aceptado") {
        activarCookiesNoEsenciales();
    }

    // Evento al hacer clic en Aceptar
    if (btnAceptar) {
        btnAceptar.addEventListener("click", function () {
            setCookie("cookie_consent", "aceptado", 365); // Guarda la decisión por 1 año
            if (banner) banner.style.display = "none";
            activarCookiesNoEsenciales();
        });
    }

    // Evento al hacer clic en Rechazar
    if (btnRechazar) {
        btnRechazar.addEventListener("click", function () {
            setCookie("cookie_consent", "rechazado", 365); // Guarda el rechazo por 1 año
            if (banner) banner.style.display = "none";
            desactivarCookiesNoEsenciales();
        });
    }
});

// Carga e inicializa Google Analytics dinámicamente
function activarCookiesNoEsenciales() {
    if (document.getElementById("ga-script")) return;

    // 1. Inyectar la etiqueta externa de Google Analytics en el <head>
    const script = document.createElement("script");
    script.id = "ga-script";
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
    document.head.appendChild(script);

    // 2. Inicializar la configuración de rastreo
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = gtag;

    gtag('js', new Date());
    gtag('config', GA_MEASUREMENT_ID);

    console.log("Google Analytics activado correctamente.");
}

// Lógica cuando el usuario rechaza las cookies
function desactivarCookiesNoEsenciales() {
    console.log("Cookies no esenciales rechazadas. Solo se mantendrán las cookies esenciales de sesión.");
}