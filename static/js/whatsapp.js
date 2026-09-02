// Manejo del menú desplegable de WhatsApp en el pie de página
document.addEventListener('DOMContentLoaded', () => {
    const whatsappBoton = document.querySelector('footer .Whatsapp-desplegable');
    const whatsappMenu = document.querySelector('footer .Whatsapp-menu');

    if (whatsappBoton && whatsappMenu) {
        whatsappBoton.addEventListener('click', (e) => {
            e.stopPropagation();
            whatsappMenu.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!whatsappMenu.contains(e.target) && !whatsappBoton.contains(e.target)) {
                whatsappMenu.classList.remove('active');
            }
        });
    }
});