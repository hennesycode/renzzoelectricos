// UI utilities for Caja dashboard
document.addEventListener('DOMContentLoaded', function(){
    // Actualizar tiempo de caja abierta
    const tiempoElement = document.getElementById('tiempo-abierta');
    if (tiempoElement) {
        const fechaApertura = new Date(tiempoElement.dataset.fecha);
        function actualizarTiempo(){
            const ahora = new Date();
            const diferencia = ahora - fechaApertura;
            const horas = Math.floor(diferencia / (1000 * 60 * 60));
            const minutos = Math.floor((diferencia % (1000 * 60 * 60)) / (1000 * 60));
            tiempoElement.textContent = `${horas}h ${minutos}m`;
        }
        actualizarTiempo();
        setInterval(actualizarTiempo, 60000);
    }

    // NOTA: Los event listeners para los botones de caja están en:
    // - abrir_ajax.js (btn-open-caja)
    // - cerrar_ajax.js (btn-close-caja)
    // - movimiento_ajax.js (btn-new-movement-ingreso, btn-new-movement-egreso)
});
