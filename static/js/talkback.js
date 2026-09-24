(function () {
    // Evitar múltiples ejecuciones del script en la misma ventana
    if (window.__dominiosfull_talkback_installed) {
        return;
    }
    window.__dominiosfull_talkback_installed = true;

    const ENABLED_KEY = 'dominiosfull_talkback_enabled';
    const PROMPT_SEEN_KEY = 'dominiosfull_talkback_prompt_seen';
    const originalConfirm = window.confirm ? window.confirm.bind(window) : null;

    let talkbackEnabled = localStorage.getItem(ENABLED_KEY) === 'true';
    let promptSeen = localStorage.getItem(PROMPT_SEEN_KEY) === 'true';
    let listenersAttached = false;
    let toggleButton = null;
    let _ultimaLectura = { texto: '', tiempo: 0 };

    function limpiarTextoTalkback(texto) {
        return texto.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
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

        if ((texto.includes('$') || texto.toUpperCase().includes('COP')) && !textoLimpio.toLowerCase().includes('pesos')) {
            textoLimpio += ' pesos';
        }

        if (!textoLimpio) return;

        try {
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(textoLimpio);
            msg.lang = 'es-ES';
            window.speechSynthesis.speak(msg);
        } catch (e) {
            console.error('Error al reproducir audio con SpeechSynthesis:', e);
        }
    }

    function guardarEstado() {
        try {
            localStorage.setItem(ENABLED_KEY, talkbackEnabled ? 'true' : 'false');
            localStorage.setItem(PROMPT_SEEN_KEY, promptSeen ? 'true' : 'false');
        } catch (e) {
            console.warn('No se pudo guardar el estado en localStorage:', e);
        }
    }

    function getTextoLegible(elemento) {
        if (!elemento) return '';
        if (elemento.closest && elemento.closest('#talkback-toggle')) return '';

        // Evaluación de elementos SELECT
        if (elemento.tagName === 'SELECT') {
            const opcionSeleccionada = elemento.options[elemento.selectedIndex];
            const textoOpcion = opcionSeleccionada ? opcionSeleccionada.text.trim() : '';
            return `Opción seleccionada: ${textoOpcion}. Use las teclas de flechas arriba y abajo para cambiar el ordenamiento.`;
        }

        // Evaluación de elementos de entrada de datos (input, textarea)
        if (['INPUT', 'TEXTAREA'].includes(elemento.tagName)) {
            if (['hidden', 'submit', 'button'].includes(elemento.type)) {
                return elemento.value || '';
            }

            // Excepción específica para Magic Link
            const contenedorMagicLink = elemento.closest('.magic-link, [id*="magic"], form[action*="magic"]');
            const esSeccionMagicLink = contenedorMagicLink || (document.body && document.body.innerText.includes('Entrar con Magic Link') && elemento.name !== 'password');
            if (esSeccionMagicLink && (elemento.type === 'email' || elemento.name === 'email' || (elemento.id && elemento.id.includes('magic')) || (elemento.placeholder && elemento.placeholder.toLowerCase().includes('correo')))) {
                return 'Ingresa tu correo para Magic Link';
            }

            // Excepción específica para confirmación de contraseña
            if (elemento.id === 'confirmar' || elemento.name === 'confirmar' || (elemento.id && elemento.id.includes('confirm')) || (elemento.getAttribute('aria-label') && elemento.getAttribute('aria-label').toLowerCase().includes('confirma'))) {
                return 'Confirma tu contraseña';
            }

            let nombreCampo = '';

            // Búsqueda del texto mediante etiqueta label asociada por ID
            if (elemento.id) {
                const labelAsociado = document.querySelector(`label[for="${CSS.escape(elemento.id)}"]`);
                if (labelAsociado && labelAsociado.innerText.trim()) {
                    nombreCampo = labelAsociado.innerText.replace(/\*/g, '').trim();
                }
            }

            // Búsqueda del texto mediante etiqueta label contenedora
            if (!nombreCampo) {
                const parentLabel = elemento.closest('label');
                if (parentLabel && parentLabel.innerText.trim()) {
                    nombreCampo = parentLabel.innerText.replace(/\*/g, '').trim();
                }
            }

            // Búsqueda del texto en atributos placeholder o aria-label
            if (!nombreCampo) {
                nombreCampo = elemento.getAttribute('placeholder') || elemento.getAttribute('aria-label') || '';
            }

            nombreCampo = nombreCampo.replace(/^(ingresa tu|confirma tu)\s+/i, '').trim().toLowerCase();

            if (nombreCampo) {
                return `Ingresa tu ${nombreCampo}`;
            }
        }

        // Evaluación de atributos de accesibilidad e imágenes
        const ariaLabel = elemento.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

        if (elemento.tagName === 'IMG') return elemento.getAttribute('alt') || '';

        return (elemento.innerText || elemento.textContent || '').replace(/\s+/g, ' ').trim();
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

    function manejarInteraccion(evento) {
        if (!talkbackEnabled) return;

        const elemento = evento.target;
        if (!elemento || !elemento.closest) return;

        let texto = '';

        // Evento de cambio directo en elementos desplegables (SELECT)
        if (evento.type === 'change' && elemento.tagName === 'SELECT') {
            const opcion = elemento.options[elemento.selectedIndex];
            if (opcion) {
                texto = `Ordenado por: ${opcion.text.trim()}`;
            }
        } 
        // Evaluación de interacción con filas de dominios (.fila-dominio)
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
            // Evaluación de interacción con tarjetas de Hosting y VPS
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
                    const textoTarjeta = tarjeta.innerText;
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
                    const textoTarjeta = tarjeta.innerText;
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
                    const objetivo = elemento.closest('h1, h2, h3, p, li, td, span, input, textarea, select, [role="button"]');
                    if (!objetivo) return;
                    texto = getTextoLegible(objetivo);
                }
            }
        }

        if (!texto) return;

        try {
            const ahora = Date.now();
            const textoNorm = texto.replace(/\s+/g, ' ').trim().toLowerCase();
            if (_ultimaLectura.texto === textoNorm && (ahora - _ultimaLectura.tiempo) < 800) {
                return;
            }
            _ultimaLectura.texto = textoNorm;
            _ultimaLectura.tiempo = ahora;
        } catch (e) {}

        setTimeout(() => hablar(texto), 60);
    }

    function adjuntarListeners() {
        if (listenersAttached) return;
        document.addEventListener('mousedown', manejarInteraccion, true);
        document.addEventListener('focusin', manejarInteraccion, true);
        document.addEventListener('change', manejarInteraccion, true);
        listenersAttached = true;
    }

    function quitarListeners() {
        if (!listenersAttached) return;
        document.removeEventListener('mousedown', manejarInteraccion, true);
        document.removeEventListener('focusin', manejarInteraccion, true);
        document.removeEventListener('change', manejarInteraccion, true);
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

    function inicializar() {
        crearBoton();
        actualizarBoton();

        if (talkbackEnabled) {
            adjuntarListeners();
        }

        // Interceptación de confirm para invocación manual si aplica
        window.confirm = function (mensaje) {
            if (mensaje && /función de voz|TalkBack|navegación por voz|modo de voz|voz/i.test(mensaje)) {
                return mostrarPreguntaInicial();
            }
            return originalConfirm ? originalConfirm(mensaje) : false;
        };

        // Verificación retrasada para el diálogo inicial si no se ha mostrado
        if (!promptSeen && !talkbackEnabled) {
            setTimeout(() => {
                if (!promptSeen) {
                    mostrarPreguntaInicial();
                }
            }, 800);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar, { once: true });
    } else {
        inicializar();
    }

    // Método global de lectura manual externa
    window.decir = function (texto, respetarEstado = true) {
        hablar(texto, respetarEstado);
    };
}());