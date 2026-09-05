document.addEventListener('DOMContentLoaded', () => {
    const listaDominios = document.getElementById('lista-dominios');
    if (!listaDominios) return;

    // Guardar el orden original exacto con el que la plantilla renderizó los dominios
    const filasDominios = Array.from(listaDominios.querySelectorAll('.fila-dominio'));
    filasDominios.forEach((fila, index) => {
        fila.dataset.ordenOriginal = index;
    });

    const selectOrden = document.getElementById('ordenar-dominios');
    const btnsFiltro = document.querySelectorAll('.btn-filtro');

    // Función para ordenar las filas
    function ordenarDominios(criterio) {
        const filasActuales = Array.from(listaDominios.querySelectorAll('.fila-dominio'));

        filasActuales.sort((a, b) => {
            if (criterio === 'precio-asc') {
                return parseFloat(a.dataset.precio) - parseFloat(b.dataset.precio);
            } else if (criterio === 'precio-desc') {
                return parseFloat(b.dataset.precio) - parseFloat(a.dataset.precio);
            } else if (criterio === 'nombre-asc') {
                return a.dataset.nombre.localeCompare(b.dataset.nombre);
            } else if (criterio === 'nombre-desc') {
                return b.dataset.nombre.localeCompare(a.dataset.nombre);
            } else {
                // 'default' / Predeterminado: Restaura el orden inicial asignado
                return parseInt(a.dataset.ordenOriginal) - parseInt(b.dataset.ordenOriginal);
            }
        });

        // Reinsertar en el contenedor con la nueva secuencia
        filasActuales.forEach(fila => listaDominios.appendChild(fila));
    }

    // Función para filtrar por tipo (Populares / Todos)
    function filtrar(tipo, botonActivo) {
        btnsFiltro.forEach(btn => btn.classList.remove('activo'));
        botonActivo.classList.add('activo');

        filasDominios.forEach(fila => {
            if (tipo === 'popular') {
                fila.style.display = fila.classList.contains('popular') ? '' : 'none';
            } else {
                fila.style.display = '';
            }
        });
    }

    // Escuchador de eventos para el selector de orden
    if (selectOrden) {
        selectOrden.addEventListener('change', (e) => {
            ordenarDominios(e.target.value);
        });
    }

    // Escuchadores de eventos para los botones de filtrado
    btnsFiltro.forEach(btn => {
        btn.addEventListener('click', () => {
            const tipo = btn.getAttribute('data-filtro');
            filtrar(tipo, btn);
        });
    });
});