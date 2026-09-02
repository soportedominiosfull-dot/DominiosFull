// Funciones para ordenamiento y filtrado de dominios
function obtenerPrecio(fila) {
    const precio = Number(fila.dataset.precio || 0);
    return Number.isFinite(precio) ? precio : 0;
}

function ordenarDominios(criteria) {
    const lista = document.getElementById('lista-dominios');
    if (!lista) return;

    const filas = Array.from(lista.querySelectorAll('.fila-dominio'));
    const filasVisibles = filas.filter(fila => !fila.classList.contains('sin-dominios') && window.getComputedStyle(fila).display !== 'none');
    const filasOcultas = filas.filter(fila => fila.classList.contains('sin-dominios') || window.getComputedStyle(fila).display === 'none');

    const filasOrdenadas = [...filasVisibles];

    if (criteria === 'precio-asc') {
        filasOrdenadas.sort((a, b) => obtenerPrecio(a) - obtenerPrecio(b));
    } else if (criteria === 'precio-desc') {
        filasOrdenadas.sort((a, b) => obtenerPrecio(b) - obtenerPrecio(a));
    } else if (criteria === 'nombre-asc') {
        filasOrdenadas.sort((a, b) => (a.dataset.nombre || '').localeCompare(b.dataset.nombre || '', 'es', { sensitivity: 'base' }));
    } else if (criteria === 'nombre-desc') {
        filasOrdenadas.sort((a, b) => (b.dataset.nombre || '').localeCompare(a.dataset.nombre || '', 'es', { sensitivity: 'base' }));
    }

    filas.forEach(fila => fila.remove());
    [...filasOrdenadas, ...filasOcultas].forEach(fila => lista.appendChild(fila));
}

function filtrar(categoria, btn) {
    document.querySelectorAll('.filtros .btn-filtro').forEach(b => b.classList.remove('activo'));
    btn.classList.add('activo');

    const lista = document.getElementById('lista-dominios');
    lista?.classList.toggle('mostrar-todos', categoria === 'todos');

    document.querySelectorAll('#lista-dominios .fila-dominio').forEach(fila => {
        if (fila.classList.contains('sin-dominios')) {
            fila.style.display = 'grid';
            return;
        }

        if (categoria === 'todos') {
            fila.style.display = 'grid';
        } else {
            fila.style.display = fila.classList.contains('popular') ? 'grid' : 'none';
        }
    });

    ordenarDominios(document.getElementById('ordenar-dominios')?.value || 'default');
}

document.addEventListener('DOMContentLoaded', () => {
    const botonPopulares = document.querySelector('.filtros .btn-filtro');
    if (botonPopulares) filtrar('popular', botonPopulares);
});