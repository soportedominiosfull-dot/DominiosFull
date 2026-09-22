// Maneja la desaparición progresiva de las notificaciones tipo toast
const elementosToast = document.querySelectorAll('.toast');

elementosToast.forEach((toast) => {
    setTimeout(() => {
        toast.classList.add('toast-hide');

        toast.addEventListener('transitionend', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }, 5000);
});

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