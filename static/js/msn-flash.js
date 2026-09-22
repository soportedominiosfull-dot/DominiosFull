// Control global de la duración de notificaciones tipo Toast / Flash
document.addEventListener('DOMContentLoaded', () => {
    const elementosToast = document.querySelectorAll('.toast, .mensaje-flash, .alert');

    elementosToast.forEach((toast) => {
        // Evita duplicar el temporizador si ya fue procesado por otro script
        if (toast.dataset.timerIniciado) return;
        toast.dataset.timerIniciado = "true";

        setTimeout(() => {
            // Aplica animación de desvanecimiento si existe la clase en tu CSS
            toast.classList.add('toast-hide');
            toast.style.transition = 'opacity 0.5s ease';
            toast.style.opacity = '0';

            // Elimina el elemento del HTML tras completarse la animación
            toast.addEventListener('transitionend', () => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, { once: true });

            // Respaldos por si la transición CSS no se dispara
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 600);
        }, 5000); //SEGUNDOS (5000 = 5 segundos)
    });
});