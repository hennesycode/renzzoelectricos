// movimiento_ajax.js - Modal SIMPLIFICADO para registrar movimientos de entrada/salida
// Solo apertura y cierre usan denominaciones de billetes y monedas
// Los movimientos normales (INGRESO/EGRESO) usan input simple de monto

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function fetchTiposMovimiento(tipo = null){
    let url = window.CAJA_URLS.tipos_movimiento;
    if (tipo) {
        url += `?tipo=${tipo}`;
    }
    const resp = await fetch(url);
    const data = await resp.json();
    if (resp.ok && data.success) return data.tipos;
    return [];
}

async function fetchTiposMovimiento(tipo = null){
    let url = window.CAJA_URLS.tipos_movimiento;
    if (tipo) {
        url += `?tipo=${tipo}`;
    }
    const resp = await fetch(url);
    const data = await resp.json();
    if (resp.ok && data.success) return data.tipos;
    return [];
}

/**
 * Modal SIMPLIFICADO para registrar movimientos
 * Solo pide: Categoría, Monto, Descripción y Referencia
 * NO usa denominaciones (eso es solo para apertura/cierre)
 */
async function openNuevoMovimientoModal(tipoPreseleccionado = null){
    // Cargar tipos de movimiento filtrados por el tipo (INGRESO o EGRESO)
    const tipos = await fetchTiposMovimiento(tipoPreseleccionado);
    
    const tipoOptions = tipos.map(t => `<option value="${t.id}">${t.nombre}</option>`).join('');
    
    // Determinar título, icono y colores según el tipo
    let titulo, icono, confirmColor, inputPlaceholder, montoLabel;
    if (tipoPreseleccionado === 'INGRESO') {
        titulo = '💰 Registrar Entrada de Dinero';
        icono = '💵';
        confirmColor = '#5c9de2';
        inputPlaceholder = 'Ej: 50000';
        montoLabel = '� Monto que Ingresa';
    } else if (tipoPreseleccionado === 'EGRESO') {
        titulo = '💸 Registrar Salida de Dinero';
        icono = '💸';
        confirmColor = '#f0d05a';
        inputPlaceholder = 'Ej: 25000';
        montoLabel = '💸 Monto que Sale';
    } else {
        titulo = 'Nuevo Movimiento';
        icono = '💰';
        confirmColor = '#3085d6';
        inputPlaceholder = 'Ej: 100000';
        montoLabel = '💰 Monto';
    }

    // HTML del formulario simplificado
    let html = '<div style="text-align: left; padding: 10px;">';
    
    // Categoría
    html += `<div style="margin-bottom: 20px;">`;
    html += `<label class="form-label" style="font-weight: 600; margin-bottom: 8px; display: block; color: #333;">📋 Categoría *</label>`;
    html += `<select id="swal-tipo-mov" class="swal2-input" style="width: 100%; padding: 12px; border-radius: 8px; border: 2px solid #ddd; font-size: 16px;">${tipoOptions}</select>`;
    html += '</div>';
    
    // Monto (input simple)
    html += `<div style="margin-bottom: 20px;">`;
    html += `<label class="form-label" style="font-weight: 600; margin-bottom: 8px; display: block; color: #333;">${montoLabel} *</label>`;
    html += `<input id="swal-monto" type="number" class="swal2-input" placeholder="${inputPlaceholder}" min="0" step="1000" style="width: 100%; padding: 12px; border-radius: 8px; border: 2px solid #ddd; font-size: 18px; font-weight: 600;">`;
    html += '<small style="color: #666; font-size: 13px;">💡 Ingresa el valor en pesos colombianos (sin puntos ni comas)</small>';
    html += '</div>';
    
    // Descripción
    html += `<div style="margin-bottom: 20px;">`;
    html += `<label class="form-label" style="font-weight: 600; margin-bottom: 8px; display: block; color: #333;">📝 Descripción</label>`;
    html += `<textarea id="swal-desc" class="swal2-textarea" placeholder="Describe el motivo del ${tipoPreseleccionado === 'INGRESO' ? 'ingreso' : 'egreso'}..." style="width: 100%; padding: 12px; border-radius: 8px; border: 2px solid #ddd; min-height: 80px; resize: vertical;"></textarea>`;
    html += '</div>';
    
    // Referencia
    html += `<div style="margin-bottom: 10px;">`;
    html += `<label class="form-label" style="font-weight: 600; margin-bottom: 8px; display: block; color: #333;">🔖 Referencia (opcional)</label>`;
    html += `<input id="swal-ref" class="swal2-input" placeholder="Número de factura, recibo, etc." style="width: 100%; padding: 12px; border-radius: 8px; border: 2px solid #ddd;">`;
    html += '</div>';
    
    html += '</div>';

    const { value } = await Swal.fire({
        title: titulo,
        html: html,
        width: 600,
        padding: '20px',
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: `✅ Registrar ${tipoPreseleccionado === 'INGRESO' ? 'Entrada' : tipoPreseleccionado === 'EGRESO' ? 'Salida' : 'Movimiento'}`,
        cancelButtonText: '❌ Cancelar',
        confirmButtonColor: confirmColor,
        cancelButtonColor: '#6c757d',
        customClass: {
            container: 'caja-modal-container',
            popup: 'caja-modal-popup'
        },
        didOpen: () => {
            // Enfocar el input de monto
            const montoInput = document.getElementById('swal-monto');
            if (montoInput) {
                montoInput.focus();
                
                // Formatear el número mientras se escribe
                montoInput.addEventListener('input', function() {
                    // Remover caracteres no numéricos
                    this.value = this.value.replace(/[^0-9]/g, '');
                });
            }
        },
        preConfirm: () => {
            const tipo_mov = document.getElementById('swal-tipo-mov').value;
            const montoInput = document.getElementById('swal-monto').value;
            const desc = document.getElementById('swal-desc').value;
            const ref = document.getElementById('swal-ref').value;
            
            // Validaciones
            if (!tipo_mov) { 
                Swal.showValidationMessage('⚠️ Selecciona una categoría'); 
                return false; 
            }
            
            const monto = parseFloat(montoInput);
            if (!montoInput || isNaN(monto) || monto <= 0) { 
                Swal.showValidationMessage('⚠️ Ingresa un monto válido mayor a cero'); 
                return false; 
            }
            
            return { tipo: tipoPreseleccionado, tipo_mov, monto, desc, ref };
        }
    });

    if (!value) return;

    // Enviar el movimiento al servidor
    try{
        const token = getCookie('csrftoken');
        const payload = {
            tipo: value.tipo,
            tipo_movimiento: value.tipo_mov,
            monto: value.monto,
            descripcion: value.desc || '',
            referencia: value.ref || ''
        };

        const resp = await fetch(window.CAJA_URLS.nuevo_movimiento, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token,
                'X-Requested-With':'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await resp.json();
        
        if (resp.ok && data.success){
            // Formatear el monto para mostrarlo
            const montoFormateado = new Intl.NumberFormat('es-CO', { 
                style: 'currency', 
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(value.monto);
            
            await Swal.fire({
                icon:'success',
                title:'✅ Registrado Correctamente',
                html: `<p style="font-size: 16px; margin: 10px 0;">
                    ${tipoPreseleccionado === 'INGRESO' ? '💵 Entrada' : '💸 Salida'} de <strong>${montoFormateado}</strong>
                </p>
                <p style="color: #666;">${data.message}</p>`,
                timer: 2000,
                showConfirmButton: false
            });
            
            // Recargar página para actualizar totales
            window.location.href = window.CAJA_URLS.dashboard;
        } else {
            Swal.fire({
                icon:'error',
                title:'❌ Error al Registrar',
                text: data.error || 'No se pudo registrar el movimiento',
                confirmButtonColor: '#d33'
            });
        }
    }catch(err){
        console.error('Error al registrar movimiento:', err);
        Swal.fire({
            icon:'error',
            title:'❌ Error de Conexión',
            text:'No se pudo conectar con el servidor. Verifica tu conexión a internet.',
            confirmButtonColor: '#d33'
        });
    }
}

// Attach handlers
document.addEventListener('DOMContentLoaded', function(){
    const btnNuevo = document.getElementById('btn-new-movement');
    const btnIngreso = document.getElementById('btn-new-movement-ingreso');
    const btnEgreso = document.getElementById('btn-new-movement-egreso');
    
    if (btnNuevo) btnNuevo.addEventListener('click', () => openNuevoMovimientoModal());
    if (btnIngreso) btnIngreso.addEventListener('click', () => openNuevoMovimientoModal('INGRESO'));
    if (btnEgreso) btnEgreso.addEventListener('click', () => openNuevoMovimientoModal('EGRESO'));
});
