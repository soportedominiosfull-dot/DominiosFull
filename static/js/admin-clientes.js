// Controla la apertura y cierre de la barra lateral de navegación
const botonMenu = document.getElementById('btnMenu');
const barraLateral = document.getElementById('sidebar');

if (botonMenu && barraLateral) {
    botonMenu.onclick = () => barraLateral.classList.toggle('active');
}

// Despliega la ventana modal asignando los datos del cliente seleccionado
function abrirModalSuspender(id, nombre) {
    document.getElementById('modalTitulo').innerText = `Suspender a ${nombre} (ID: ${id})`;
    document.getElementById('formSuspender').action = `/suspender-cliente/${id}`;
    document.getElementById('modalSuspension').style.display = 'block';
    document.getElementById('justificacion').focus();
    
    if (typeof modoVozActivado !== 'undefined' && modoVozActivado) {
        decir(`Ventana emergente abierta. Escriba la justificación para suspender a ${nombre}`);
    }
}

// Oculta la ventana modal de suspensión
function cerrarModal() {
    document.getElementById('modalSuspension').style.display = 'none';
}

// FILTROS DE BÚSQUEDA 

document.addEventListener('DOMContentLoaded', function () {
    const inputBuscarClientes = document.getElementById('inputBuscarClientes');
    const tablaClientes = document.getElementById('tablaClientes');

    if (inputBuscarClientes && tablaClientes) {
        inputBuscarClientes.addEventListener('input', function () {
            const busqueda = this.value.toLowerCase().trim();
            const filas = tablaClientes.querySelectorAll('tbody tr');

            filas.forEach(fila => {
                if (fila.querySelector('.mensaje-vacio')) return;

                const nombre = fila.children[1] ? fila.children[1].textContent.toLowerCase() : '';
                const correo = fila.children[2] ? fila.children[2].textContent.toLowerCase() : '';

                if (nombre.includes(busqueda) || correo.includes(busqueda)) {
                    fila.style.display = '';
                } else {
                    fila.style.display = 'none';
                }
            });
        });
    }
    const inputBuscarCompras = document.getElementById('inputBuscarCompras');
    const tablaCompras = document.getElementById('tablaCompras');

    if (inputBuscarCompras && tablaCompras) {
        inputBuscarCompras.addEventListener('input', function () {
            const busqueda = this.value.toLowerCase().trim();
            const filas = tablaCompras.querySelectorAll('tbody tr');

            filas.forEach(fila => {
                if (fila.querySelector('.mensaje-vacio')) return;

                const cliente = fila.children[1] ? fila.children[1].textContent.toLowerCase() : '';
                const servicio = fila.children[2] ? fila.children[2].textContent.toLowerCase() : '';

                if (cliente.includes(busqueda) || servicio.includes(busqueda)) {
                    fila.style.display = '';
                } else {
                    fila.style.display = 'none';
                }
            });
        });
    }
});