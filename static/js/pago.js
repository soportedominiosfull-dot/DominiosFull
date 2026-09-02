document.addEventListener('DOMContentLoaded', () => {
    const metodoInputs = document.querySelectorAll('input[name="metodo_pago"]');
    const datosTarjeta = document.getElementById('datos-tarjeta');
    const datosPayPal = document.getElementById('datos-paypal');
    const datosNequi = document.getElementById('datos-nequi');
    const datosDaviplata = document.getElementById('datos-daviplata');

    const camposTarjeta = datosTarjeta ? datosTarjeta.querySelectorAll('input') : [];
    const camposPayPal = datosPayPal ? datosPayPal.querySelectorAll('input') : [];
    const camposNequi = datosNequi ? datosNequi.querySelectorAll('input') : [];
    const camposDaviplata = datosDaviplata ? datosDaviplata.querySelectorAll('input') : [];

    function actualizarCamposPago() {
        const metodoSeleccionado = document.querySelector('input[name="metodo_pago"]:checked');
        const valor = metodoSeleccionado ? metodoSeleccionado.value : null;

        const mostrarTarjeta = valor && ['debito', 'credito'].includes(valor);
        const mostrarPayPal = valor === 'paypal';
        const mostrarNequi = valor === 'nequi';
        const mostrarDavi = valor === 'daviplata';

        if (datosTarjeta) datosTarjeta.style.display = mostrarTarjeta ? 'block' : 'none';
        if (datosPayPal) datosPayPal.style.display = mostrarPayPal ? 'block' : 'none';
        if (datosNequi) datosNequi.style.display = mostrarNequi ? 'block' : 'none';
        if (datosDaviplata) datosDaviplata.style.display = mostrarDavi ? 'block' : 'none';

        camposTarjeta.forEach((campo) => { campo.required = mostrarTarjeta; });
        camposPayPal.forEach((campo) => { campo.required = mostrarPayPal; });
        camposNequi.forEach((campo) => { campo.required = mostrarNequi; });
        camposDaviplata.forEach((campo) => { campo.required = mostrarDavi; });
    }

    metodoInputs.forEach((input) => {
        input.addEventListener('change', actualizarCamposPago);
    });

    actualizarCamposPago();

    // Formateo automático para fecha de vencimiento: MM/AA
    const fechaInput = document.getElementById('fecha_vencimiento');
    if (fechaInput) {
        fechaInput.addEventListener('input', (e) => {
            let v = e.target.value.replace(/[^0-9]/g, '');
            if (v.length > 4) v = v.slice(0, 4);
            if (v.length > 2) {
                v = v.slice(0, 2) + '/' + v.slice(2);
            }
            e.target.value = v;
        });

        fechaInput.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = (e.clipboardData || window.clipboardData).getData('text').replace(/[^0-9]/g, '').slice(0, 4);
            if (text.length > 2) {
                fechaInput.value = text.slice(0, 2) + '/' + text.slice(2);
            } else {
                fechaInput.value = text;
            }
        });
    }
});