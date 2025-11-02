// movimiento_ajax.js - Modal MODERNO Y MEJORADO para registrar movimientos de entrada/salida
// Solo apertura y cierre usan denominaciones de billetes y monedas
// Los movimientos normales (INGRESO/EGRESO) usan input simple de monto con diseño mejorado

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

/**
 * Modal MODERNO Y MEJORADO para registrar movimientos
 * Diseño limpio, intuitivo y completamente responsive
 */
async function openNuevoMovimientoModal(tipoPreseleccionado = null){
    // Cargar tipos de movimiento filtrados por el tipo (INGRESO o EGRESO)
    const tipos = await fetchTiposMovimiento(tipoPreseleccionado);
    
    const tipoOptions = tipos.map(t => `<option value="${t.id}">${t.nombre}</option>`).join('');
    
    // Determinar título, icono y colores según el tipo
    let titulo, icono, confirmColor, inputPlaceholder, montoLabel, bgGradient;
    if (tipoPreseleccionado === 'INGRESO') {
        titulo = 'Registrar Entrada de Dinero';
        icono = '💰';
        confirmColor = '#4CAF50';
        inputPlaceholder = '50000';
        montoLabel = 'Monto que Ingresa';
        bgGradient = 'linear-gradient(135deg, #43cea2 0%, #185a9d 100%)';
    } else if (tipoPreseleccionado === 'EGRESO') {
        titulo = 'Registrar Salida de Dinero';
        icono = '💸';
        confirmColor = '#FF9800';
        inputPlaceholder = '25000';
        montoLabel = 'Monto que Sale';
        bgGradient = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    } else {
        titulo = 'Nuevo Movimiento';
        icono = '💰';
        confirmColor = '#3085d6';
        inputPlaceholder = '100000';
        montoLabel = 'Monto';
        bgGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }

    // HTML del formulario moderno y mejorado
    let html = `
    <style>
        .modern-modal-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 0;
            margin: 0;
        }
        .modal-header-custom {
            background: ${bgGradient};
            color: white;
            padding: 30px 25px;
            margin: -20px -20px 30px -20px;
            border-radius: 15px 15px 0 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .modal-header-custom::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="10" cy="10" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="50" r="1.5" fill="white" opacity="0.1"/><circle cx="90" cy="20" r="1" fill="white" opacity="0.1"/><circle cx="30" cy="80" r="1.2" fill="white" opacity="0.1"/><circle cx="70" cy="70" r="1" fill="white" opacity="0.1"/></svg>');
            background-size: 50px 50px;
            opacity: 0.3;
        }
        .modal-icon {
            width: 80px;
            height: 80px;
            background: rgba(255,255,255,0.25);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            margin-bottom: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            position: relative;
            z-index: 1;
        }
        .modal-title-custom {
            font-size: 26px;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            position: relative;
            z-index: 1;
        }
        .form-group-modern {
            margin-bottom: 25px;
            text-align: left;
        }
        .form-label-modern {
            font-weight: 600;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #2c3e50;
            font-size: 15px;
        }
        .form-label-icon {
            font-size: 18px;
        }
        .form-control-modern {
            width: 100%;
            padding: 15px 20px;
            border-radius: 12px;
            border: 2px solid #e0e0e0;
            font-size: 16px;
            transition: all 0.3s ease;
            box-sizing: border-box;
            background: #f8f9fa;
            font-family: inherit;
        }
        .form-control-modern:focus {
            outline: none;
            border-color: ${confirmColor};
            background: white;
            box-shadow: 0 0 0 4px ${confirmColor}20;
            transform: translateY(-1px);
        }
        .form-control-modern:hover {
            border-color: #c0c0c0;
        }
        .form-control-monto {
            font-size: 28px !important;
            font-weight: 700;
            text-align: center;
            letter-spacing: 1px;
            color: ${confirmColor};
            padding: 20px !important;
        }
        .form-hint {
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
            padding-left: 5px;
        }
        .select-modern {
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23343a40' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 15px center;
            background-size: 16px 12px;
            padding-right: 45px !important;
            appearance: none;
            cursor: pointer;
        }
        textarea.form-control-modern {
            resize: vertical;
            min-height: 100px;
            font-family: inherit;
            line-height: 1.6;
        }
        .required-mark {
            color: #e74c3c;
            font-weight: bold;
            margin-left: 2px;
        }
        
        /* Estilos para botones mejorados */
        .swal2-actions {
            gap: 15px !important;
        }
        .swal2-confirm, .swal2-cancel {
            padding: 14px 35px !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            border: none !important;
            transition: all 0.3s ease !important;
            min-width: 150px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
        }
        .swal2-confirm:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.25) !important;
        }
        .swal2-cancel:hover {
            background-color: #7f8c8d !important;
            transform: translateY(-2px) !important;
        }
        
        /* Animación de entrada */
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .form-group-modern {
            animation: slideDown 0.3s ease forwards;
        }
        .form-group-modern:nth-child(1) { animation-delay: 0.1s; }
        .form-group-modern:nth-child(2) { animation-delay: 0.2s; }
        .form-group-modern:nth-child(3) { animation-delay: 0.3s; }
        .form-group-modern:nth-child(4) { animation-delay: 0.4s; }
    </style>
    
    <div class="modern-modal-container">
        <div class="modal-header-custom">
            <div class="modal-icon">${icono}</div>
            <h2 class="modal-title-custom">${titulo}</h2>
        </div>
        
        <div class="form-group-modern">
            <label class="form-label-modern">
                <span class="form-label-icon">📋</span>
                <span>Categoría <span class="required-mark">*</span></span>
            </label>
            <select id="swal-tipo-mov" class="form-control-modern select-modern">
                ${tipoOptions}
            </select>
        </div>
        
        <div class="form-group-modern">
            <label class="form-label-modern">
                <span class="form-label-icon">${tipoPreseleccionado === 'INGRESO' ? '💵' : '💸'}</span>
                <span>${montoLabel} <span class="required-mark">*</span></span>
            </label>
            <input 
                id="swal-monto" 
                type="text" 
                class="form-control-modern form-control-monto" 
                placeholder="${inputPlaceholder}"
                autocomplete="off"
            >
            <div class="form-hint">
                <span>💡</span>
                <span>Ingresa el valor en pesos colombianos</span>
            </div>
        </div>
        
        <div class="form-group-modern">
            <label class="form-label-modern">
                <span class="form-label-icon">📝</span>
                <span>Descripción</span>
            </label>
            <textarea 
                id="swal-desc" 
                class="form-control-modern" 
                placeholder="Describe el motivo del ${tipoPreseleccionado === 'INGRESO' ? 'ingreso' : 'egreso'}..."
            ></textarea>
        </div>
        
        <div class="form-group-modern">
            <label class="form-label-modern">
                <span class="form-label-icon">🔖</span>
                <span>Referencia (opcional)</span>
            </label>
            <input 
                id="swal-ref" 
                type="text" 
                class="form-control-modern" 
                placeholder="Número de factura, recibo, etc."
            >
        </div>
    </div>
    `;

    const { value } = await Swal.fire({
        html: html,
        width: 650,
        padding: '20px',
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: `✅ Registrar ${tipoPreseleccionado === 'INGRESO' ? 'Entrada' : tipoPreseleccionado === 'EGRESO' ? 'Salida' : 'Movimiento'}`,
        cancelButtonText: '✖ Cancelar',
        confirmButtonColor: confirmColor,
        cancelButtonColor: '#95a5a6',
        buttonsStyling: true,
        showClass: {
            popup: 'animate__animated animate__fadeInDown animate__faster'
        },
        hideClass: {
            popup: 'animate__animated animate__fadeOutUp animate__faster'
        },
        didOpen: () => {
            // Formateo inteligente del input de monto
            const montoInput = document.getElementById('swal-monto');
            if (montoInput) {
                montoInput.focus();
                
                // Formatear mientras escribe
                montoInput.addEventListener('input', function(e) {
                    let value = this.value.replace(/[^\d]/g, '');
                    if (value) {
                        // Formatear con separadores de miles
                        value = parseInt(value).toLocaleString('es-CO');
                    }
                    this.value = value ? `$ ${value}` : '';
                });
                
                // Limpiar formato al hacer focus para mejor UX
                montoInput.addEventListener('focus', function() {
                    if (this.value === '$ ') {
                        this.value = '';
                    }
                    this.select();
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
                Swal.showValidationMessage('⚠️ Por favor selecciona una categoría'); 
                return false; 
            }
            
            // Limpiar el monto de formato
            const montoLimpio = montoInput.replace(/[^\d]/g, '');
            const monto = parseFloat(montoLimpio);
            
            if (!montoLimpio || isNaN(monto) || monto <= 0) { 
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
                title:'✅ ¡Registrado Correctamente!',
                html: `
                    <div style="padding: 15px; text-align: center;">
                        <p style="font-size: 18px; margin: 15px 0; font-weight: 600; color: #2c3e50;">
                            ${tipoPreseleccionado === 'INGRESO' ? '💵 Entrada' : '💸 Salida'} de 
                            <span style="color: ${confirmColor}; font-size: 24px; font-weight: 700;">${montoFormateado}</span>
                        </p>
                        <p style="color: #7f8c8d; font-size: 14px;">${data.message}</p>
                    </div>
                `,
                timer: 2500,
                showConfirmButton: false,
                timerProgressBar: true
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
