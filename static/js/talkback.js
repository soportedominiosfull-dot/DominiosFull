(function () {
    // Evitar múltiples ejecuciones del script en la misma ventana
    if (window.__dominiosfull_talkback_installed) {
        return;
    }
    window.__dominiosfull_talkback_installed = true;

    const ENABLED_KEY = 'dominiosfull_talkback_enabled';
    const PROMPT_SEEN_KEY = 'dominiosfull_talkback_prompt_seen';
    const originalConfirm = window.confirm ? window.confirm.bind(window) : null;

    // Métodos de almacenamiento con blindaje de excepciones (Modo Incógnito / Iframe)
    function getStorage(key) {
        try {
            return localStorage.getItem(key);
        } catch (e) {
            return null;
        }
    }

    function setStorage(key, val) {
        try {
            localStorage.setItem(key, String(val));
        } catch (e) {
            console.warn('No se pudo escribir en almacenamiento local:', e);
        }
    }

    let talkbackEnabled = getStorage(ENABLED_KEY) === 'true';
    let promptSeen = getStorage(PROMPT_SEEN_KEY) === 'true';
    let listenersAttached = false;
    let toggleButton = null;
    let _ultimaLectura = { texto: '', tiempo: 0 };

    function limpiarTextoTalkback(texto) {
        return String(texto || '').replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
    }

    function hasSpeechSupport() {
        return typeof window !== 'undefined' && 
               'speechSynthesis' in window && 
               typeof window.SpeechSynthesisUtterance === 'function';
    }

    function hablar(texto, respetarEstado = true) {
        if (!hasSpeechSupport() || !texto) return;
        if (respetarEstado && !talkbackEnabled) return;

        let textoLimpio = limpiarTextoTalkback(texto)
            .replace(/\.([a-z0-9]+)\b/gi, ' punto $1')
            .replace(/\$/g, '')
            .replace(/COP/gi, '')
            .replace(/\s+/g, ' ')
            .trim();

        if ((String(texto).includes('$') || String(texto).toUpperCase().includes('COP')) && !textoLimpio.toLowerCase().includes('pesos')) {
            textoLimpio += ' pesos';
        }

        if (!textoLimpio) return;

        try {
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(textoLimpio);
            msg.lang = 'es-ES';
            window.speechSynthesis.speak(msg);
        } catch (e) {
            console.error('Error en síntesis de voz:', e);
        }
    }

    function guardarEstado() {
        setStorage(ENABLED_KEY, talkbackEnabled ? 'true' : 'false');
        setStorage(PROMPT_SEEN_KEY, promptSeen ? 'true' : 'false');
    }

    function getLabelAsociadoTexto(inputEl) {
        if (!inputEl) return '';
        if (inputEl.id) {
            try {
                const labelFor = document.querySelector(`label[for="${CSS.escape(inputEl.id)}"]`);
                if (labelFor && labelFor.innerText && labelFor.innerText.trim()) {
                    return labelFor.innerText.trim();
                }
            } catch (e) {}
        }
        const parentLabel = inputEl.closest ? inputEl.closest('label') : null;
        if (parentLabel && parentLabel.innerText && parentLabel.innerText.trim()) {
            return parentLabel.innerText.trim();
        }
        return '';
    }

function getTextoLegible(elementoOriginal) {
        if (!elementoOriginal) return '';

        // 1. Normalización de contenedor interactivo (incluyendo iFrames de CAPTCHA)
        const contenedor = elementoOriginal.closest
            ? elementoOriginal.closest('button, a, summary, select, textarea, input, iframe, .g-recaptcha, [role="button"], [role="menuitem"]')
            : null;

        const el = contenedor || elementoOriginal;

        if (el.closest && el.closest('#talkback-toggle')) return '';

        // Prioridad reCAPTCHA / iFrames
if (
            el.tagName === 'IFRAME' || 
            (el.classList && el.classList.contains('g-recaptcha')) || 
            (el.src && String(el.src).includes('recaptcha')) ||
            (el.title && String(el.title).toLowerCase().includes('recaptcha')) ||
            (el.getAttribute && el.getAttribute('data-sitekey'))
        ) {
            if (window.__recaptcha_completado) return '';

            const srcStr = el.src ? String(el.src) : '';
            const titleStr = el.title ? String(el.title).toLowerCase() : '';
            if (srcStr.includes('bframe') || titleStr.includes('challenge') || titleStr.includes('desafío')) {
                return 'Desafío visual abierto. Navegue con Tab para encontrar la opción de desafío por audio.';
            }

            return 'Verificación de seguridad. Casilla No soy un robot. Presione la barra espaciadora o Enter para verificar.';
        }

        // 2. Evaluación de Botones de Opción / Radio Buttons (Calificación con Estrellas)
        if (el.tagName === 'INPUT' && el.type === 'radio') {
            const textoEstrellas = String(el.value) === '1' ? '1 estrella' : `${el.value} estrellas`;
            const labelRadio = el.getAttribute('aria-label') || el.getAttribute('title') || textoEstrellas;
            const estado = el.checked ? 'seleccionado' : 'no seleccionado, use las teclas de flechas para cambiar y seleccione con Enter';
            return `${labelRadio}, ${estado}`;
        }

        // 3. Evaluación de Casillas de Verificación (Checkboxes)
        if (el.tagName === 'INPUT' && el.type === 'checkbox') {
            const labelTexto = el.getAttribute('aria-label') || getLabelAsociadoTexto(el) || el.name || 'Casilla';
            const estado = el.checked ? 'marcado' : 'no marcado';
            return `${labelTexto}, ${estado}`;
        }

        // 4. Atributo aria-label explícito en Botones, Enlaces o Secciones
        const ariaLabel = el.getAttribute && el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) {
            return ariaLabel.trim();
        }

        // 5. Evaluación de Acordeones / Desplegables (Vista clientes)
        if (el.tagName === 'SUMMARY') {
            const details = el.parentElement;
            const esAbierto = details && details.hasAttribute('open');
            const estado = esAbierto ? 'desplegada' : 'contraída';
            const textoSummary = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
            const accion = esAbierto ? 'contraer' : 'expandir';
            return `${textoSummary}. Sección ${estado}. Presione enter o espacio para ${accion}.`;
        }

        // 6. Evaluación de Lista Desplegable (SELECT)
        if (el.tagName === 'SELECT') {
            const opcion = el.options && el.selectedIndex >= 0 ? el.options[el.selectedIndex] : null;
            const textoOpcion = opcion ? opcion.text.trim() : '';
            return `Desplegable. Opción seleccionada: ${textoOpcion}. Use las teclas de flechas para cambiar.`;
        }

        // 7. Formulario de Datos (INPUT, TEXTAREA)
        if (['INPUT', 'TEXTAREA'].includes(el.tagName)) {
            if (['hidden', 'submit', 'button', 'image'].includes(el.type)) {
                return el.value || el.getAttribute('aria-label') || '';
            }

            let labelTexto = getLabelAsociadoTexto(el);

            if (!labelTexto) {
                labelTexto = el.getAttribute('placeholder') || '';
            }

            labelTexto = labelTexto
                .replace(/^(ingresa\s+tu|confirma\s+tu|ingrese\s+su|confirme\s+su|tu|su)\s+/i, '')
                .replace(/:$/g, '')
                .replace(/\*/g, '')
                .trim();

            if (!labelTexto) {
                labelTexto = el.name || el.type || 'campo de texto';
            }

            if (/^(confirmar|buscar|ingresar|escribir|seleccionar)/i.test(labelTexto)) {
                return labelTexto;
            }

            return `Ingresa tu ${labelTexto.toLowerCase()}`;
        }

        // 8. Imágenes
        if (el.tagName === 'IMG') {
            return el.getAttribute('alt') || '';
        }

        // 9. Lectura general de texto
        return (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    }

    function formatearPrecioNum(val) {
        if (!val) return '';
        
        let textoPrecio = String(val).split('/')[0];
        let num = parseInt(textoPrecio.replace(/[^\d]/g, ''), 10);
        
        if (isNaN(num) || num <= 0) return '';

        if (num % 1000 === 0 && num >= 1000) {
            let miles = num / 1000;
            return `${miles} mil`;
        }

        if (num > 1000) {
            let miles = Math.floor(num / 1000);
            let resto = num % 1000;
            return `${miles} mil ${resto}`;
        }

        return String(num);
    }

    //Evaluar servicios adquiridos (Vista clientes)
    function manejarToggle(evento) {
        if (!talkbackEnabled) return;
        const details = evento.target;
        if (!details || details.tagName !== 'DETAILS') return;

        const summary = details.querySelector('summary');
        let titulo = summary ? (summary.innerText || summary.textContent || '').replace(/\s+/g, ' ').trim() : 'Sección';
        titulo = limpiarTextoTalkback(titulo).trim();

        if (details.open) {
            hablar(`${titulo} desplegado. Usa la tecla Tab para recorrer los servicios adquiridos.`);
        } else {
            hablar(`${titulo} contraído.`);
        }
    }

    function manejarInteraccion(evento) {
        if (!talkbackEnabled) return;

        let elemento = evento.target;
                if (!elemento || elemento === document || elemento === window || !elemento.closest) {
                    elemento = document.activeElement;
                }

                if (!elemento || !elemento.closest) return;

        let texto = '';

        if (evento.type === 'change' && elemento.tagName === 'SELECT') {
            const opcion = elemento.options && elemento.selectedIndex >= 0 ? elemento.options[elemento.selectedIndex] : null;
            if (opcion) {
                texto = `Ordenado por: ${opcion.text.trim()}`;
            }
        } 
        else {
            const filaDominio = elemento.closest('.fila-dominio');

            if (filaDominio) {
                if (filaDominio.classList.contains('sin-dominios')) {
                    texto = 'No hay dominios disponibles registrados.';
                } else {
                    const rawNombre = filaDominio.dataset.nombre || filaDominio.querySelector('.nombre')?.innerText || '';
                    const rawPrecio = filaDominio.dataset.precio || '';
                    
                    let nombreExtension = rawNombre.trim();
                    let precioFormateado = formatearPrecioNum(rawPrecio);
                    
                    const tieneOferta = Boolean(filaDominio.querySelector('.badge-oferta'));
                    let textoOferta = tieneOferta ? ' en oferta' : '';

                    const esBoton = elemento.closest('.btn-carrito, a, button');

                    if (esBoton) {
                        texto = `Añadir al carrito dominio ${nombreExtension}${textoOferta}, precio ${precioFormateado} pesos por 1 Año`;
                    } else {
                        texto = `Dominio ${nombreExtension}${textoOferta}, precio ${precioFormateado} pesos por 1 Año`;
                    }
                }
            }
            else {
                const tarjeta = elemento.closest('.plan, .hosting-card, .vps-card');
                const esBotonComprar = elemento.closest('.btn-buy, a[href*="/agregar/"]');
                const esOtroEnlaceOBoton = elemento.closest('a, button, input[type="submit"], input[type="button"]');

                if (esBotonComprar && tarjeta) {
                    const h3 = tarjeta.querySelector('h3, h2');
                    let titulo = h3 ? h3.innerText.replace(/¡OFERTA!/gi, '').trim() : '';
                    
                    const precioEl = tarjeta.querySelector('.precio-oferta-card, .precio-normal-card, .precio-original-card, .price-container');
                    let precioTexto = precioEl ? formatearPrecioNum(precioEl.innerText) : '';

                    let periodoTexto = '';
                    const textoTarjeta = tarjeta.innerText || '';
                    const periodoMatch = textoTarjeta.match(/\/\s*(\d+\s*meses|\d+\s*mes|año|mes)/i);
                    if (periodoMatch) {
                        periodoTexto = ` por ${periodoMatch[1]}`;
                    }

                    if (titulo && precioTexto) {
                        texto = `Añadir al carrito plan ${titulo}, precio ${precioTexto} pesos${periodoTexto}`;
                    } else if (titulo) {
                        texto = `Añadir al carrito plan ${titulo}`;
                    } else {
                        texto = getTextoLegible(esBotonComprar);
                    }
                }
                else if (tarjeta && !esOtroEnlaceOBoton) {
                    const h3 = tarjeta.querySelector('h3, h2');
                    let titulo = '';
                    if (h3) {
                        const h3Clone = h3.cloneNode(true);
                        const badge = h3Clone.querySelector('.badge-oferta-card');
                        if (badge) badge.remove();
                        titulo = h3Clone.innerText.trim();
                    }

                    const precioEl = tarjeta.querySelector('.precio-oferta-card, .precio-normal-card, .precio-original-card, .price-container');
                    let precioTexto = precioEl ? formatearPrecioNum(precioEl.innerText) : '';

                    let periodoTexto = '';
                    const textoTarjeta = tarjeta.innerText || '';
                    const periodoMatch = textoTarjeta.match(/\/\s*(\d+\s*meses|\d+\s*mes|año|mes)/i);
                    if (periodoMatch) {
                        periodoTexto = ` por ${periodoMatch[1]}`;
                    }

                    if (titulo && precioTexto) {
                        texto = `Plan ${titulo}, precio ${precioTexto} pesos${periodoTexto}`;
                    } else {
                        texto = getTextoLegible(tarjeta);
                    }
                }
                else if (esOtroEnlaceOBoton) {
                    texto = getTextoLegible(esOtroEnlaceOBoton);
                } 
                else {
                    const objetivo = elemento.closest('h1, h2, h3, p, li, td, span, input, textarea, select, summary, details, iframe, .g-recaptcha, [role="button"]');
                    if (!objetivo) return;
                    texto = getTextoLegible(objetivo);
                }
            }
        }

        if (!texto) return;

        // Anti-rebote / Throttling a 600ms para evitar lecturas duplicadas consecutivas
        try {
            const ahora = Date.now();
            const textoNorm = String(texto).replace(/\s+/g, ' ').trim().toLowerCase();
            if (_ultimaLectura.texto === textoNorm && (ahora - _ultimaLectura.tiempo) < 600) {
                return;
            }
            _ultimaLectura.texto = textoNorm;
            _ultimaLectura.tiempo = ahora;
        } catch (e) {}

        setTimeout(() => hablar(texto), 50);
    }

function manejarBlurIframe() {
        if (!talkbackEnabled || window.__recaptcha_completado) return;
        setTimeout(() => {
            const activo = document.activeElement;
            if (activo && (
                activo.tagName === 'IFRAME' ||
                (activo.src && String(activo.src).includes('recaptcha')) ||
                (activo.title && String(activo.title).toLowerCase().includes('recaptcha')) ||
                (activo.closest && activo.closest('.g-recaptcha'))
            )) {
                const srcStr = activo.src ? String(activo.src) : '';
                const titleStr = activo.title ? String(activo.title).toLowerCase() : '';

                let textoCaptcha = 'Verificación de seguridad. Casilla No soy un robot. Presione la barra espaciadora o Enter para verificar.';

                if (srcStr.includes('bframe') || titleStr.includes('challenge') || titleStr.includes('desafío')) {
                    textoCaptcha = 'Desafío visual abierto. Navegue con Tab para encontrar la opción de desafío por audio.';
                }

                const ahora = Date.now();
                if (_ultimaLectura.texto === textoCaptcha.toLowerCase() && (ahora - _ultimaLectura.tiempo) < 4000) {
                    return;
                }

                _ultimaLectura.texto = textoCaptcha.toLowerCase();
                _ultimaLectura.tiempo = ahora;
                hablar(textoCaptcha);
            }
        }, 100);
    }

    function adjuntarListeners() {
        if (listenersAttached) return;
        document.addEventListener('mousedown', manejarInteraccion, true);
        document.addEventListener('focusin', manejarInteraccion, true);
        document.addEventListener('change', manejarInteraccion, true);
        document.addEventListener('toggle', manejarToggle, true);
        document.addEventListener('focus', manejarInteraccion, true);
        window.addEventListener('blur', manejarBlurIframe, true);
        listenersAttached = true;
    }

    function quitarListeners() {
        if (!listenersAttached) return;
        document.removeEventListener('mousedown', manejarInteraccion, true);
        document.removeEventListener('focusin', manejarInteraccion, true);
        document.removeEventListener('change', manejarInteraccion, true);
        document.removeEventListener('toggle', manejarToggle, true);
        document.removeEventListener('focus', manejarInteraccion, true);
        window.removeEventListener('blur', manejarBlurIframe, true);
        listenersAttached = false;
    }

    function actualizarBoton() {
        if (!toggleButton) return;
        toggleButton.classList.toggle('active', talkbackEnabled);
        toggleButton.setAttribute('aria-pressed', String(talkbackEnabled));
        toggleButton.setAttribute('aria-label', talkbackEnabled ? 'Desactivar TalkBack' : 'Activar TalkBack');

        const textoVisible = talkbackEnabled ? 'TalkBack ON' : 'TalkBack';
        toggleButton.innerHTML = `<span class="talkback-icon" aria-hidden="true">${talkbackEnabled ? '🔊' : '🔈'}</span><span class="talkback-text">${textoVisible}</span>`;
    }

    function crearBoton() {
        if (toggleButton || !document.body) return;

        toggleButton = document.createElement('button');
        toggleButton.id = 'talkback-toggle';
        toggleButton.type = 'button';
        toggleButton.className = 'talkback-toggle';
        toggleButton.setAttribute('role', 'button');
        toggleButton.setAttribute('tabindex', '0');

        toggleButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            talkbackEnabled = !talkbackEnabled;
            promptSeen = true;
            guardarEstado();
            actualizarBoton();

            if (talkbackEnabled) {
                adjuntarListeners();
                hablar('Modo de voz activado.', false);
            } else {
                quitarListeners();
                if (hasSpeechSupport()) {
                    window.speechSynthesis.cancel();
                }
                hablar('Modo de voz desactivado.', false);
            }
        });

        document.body.appendChild(toggleButton);
        actualizarBoton();
    }

    function establecerEstado(nextEnabled) {
        talkbackEnabled = Boolean(nextEnabled);
        promptSeen = true;
        guardarEstado();
        actualizarBoton();

        if (talkbackEnabled) {
            adjuntarListeners();
        } else {
            quitarListeners();
            if (hasSpeechSupport()) {
                window.speechSynthesis.cancel();
            }
        }
    }

    function mostrarPreguntaInicial() {
        if (promptSeen) return talkbackEnabled;

        promptSeen = true;
        let aceptado = false;
        
        if (originalConfirm) {
            aceptado = originalConfirm('DominiosFull incluye un modo de voz accesible. ¿Deseas activarlo ahora?');
        }

        establecerEstado(aceptado);
        return aceptado;
    }

    function anunciarMensajesFlash() {
        if (!talkbackEnabled) return;
        
        // Margen de tiempo para permitir la inicialización de msn-flash.js y la recarga del navegador
        setTimeout(() => {
            const alertas = document.querySelectorAll('.toast, .mensaje-flash, [role="alert"]');
            alertas.forEach(alerta => {
                const texto = (alerta.innerText || alerta.textContent || '').trim();
                if (texto) {
                    hablar(`Notificación: ${texto}`);
                }
            });
        }, 800);
    }

    function inicializar() {
        crearBoton();
        actualizarBoton();

        if (talkbackEnabled) {
            adjuntarListeners();
        }

        window.confirm = function (mensaje) {
            if (mensaje && /función de voz|TalkBack|navegación por voz|modo de voz|voz/i.test(mensaje)) {
                return mostrarPreguntaInicial();
            }
            return originalConfirm ? originalConfirm(mensaje) : false;
        };

        if (!promptSeen && !talkbackEnabled) {
            setTimeout(() => {
                if (!promptSeen) {
                    mostrarPreguntaInicial();
                }
            }, 800);
        }

        // Anunciar alertas flash activas tras recarga
        anunciarMensajesFlash();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar, { once: true });
    } else {
        inicializar();
    }

    window.decir = function (texto, respetarEstado = true) {
        hablar(texto, respetarEstado);
    };

    window.recaptchaVerificado = function () {
            window.__recaptcha_completado = true;
            setTimeout(() => {
                hablar('Verificación completada con éxito.');
            }, 200);
        };
}());