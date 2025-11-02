// movimiento_ajax.js - modal para registrar nuevo movimiento vía AJAX

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

async function fetchDenominaciones(){
    const resp = await fetch(window.CAJA_URLS.denominaciones);
    const data = await resp.json();
    if (resp.ok && data.success) return data.denominaciones;
    return [];
}

async function openNuevoMovimientoModal(tipoPreseleccionado = null){
    // Cargar tipos de movimiento filtrados por el tipo (INGRESO o EGRESO)
    const tipos = await fetchTiposMovimiento(tipoPreseleccionado);
    const denoms = await fetchDenominaciones();
    
    // Separar y ordenar billetes y monedas
    const billetes = denoms.filter(d => d.tipo.toUpperCase() === 'BILLETE').sort((a, b) => b.valor - a.valor);
    const monedas = denoms.filter(d => d.tipo.toUpperCase() === 'MONEDA').sort((a, b) => b.valor - a.valor);
    
    const tipoOptions = tipos.map(t => `<option value="${t.id}">${t.nombre}</option>`).join('');
    
    // Determinar título, icono y colores según el tipo
    let titulo, icono, confirmColor, totalIcon;
    if (tipoPreseleccionado === 'INGRESO') {
        titulo = '💰 Registrar Entrada';
        icono = '💵';
        confirmColor = '#5c9de2';
        totalIcon = '💰';
    } else if (tipoPreseleccionado === 'EGRESO') {
        titulo = '💸 Registrar Salida';
        icono = '💸';
        confirmColor = '#f0d05a';
        totalIcon = '💸';
    } else {
        titulo = 'Nuevo Movimiento';
        icono = '💰';
        confirmColor = '#3085d6';
        totalIcon = '💰';
    }

    let html = '<div style="text-align: left;">';
    html += `<label class="form-label" style="font-weight: 600; margin-bottom: 8px; display: block;">Categoría</label>`;
    html += `<select id="swal-tipo-mov" class="swal2-input" style="width: 100%; margin-bottom: 15px;">${tipoOptions}</select>`;
    html += '</div>';
    
    html += '<div class="denominaciones-container" style="text-align: left;">';
    
    // Billetes
    if (billetes.length > 0) {
        html += '<h4 class="denom-group">💵 Billetes</h4>';
        html += '<div class="denom-grid">';
        billetes.forEach(d => {
            const valorFormateado = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(d.valor);
            html += `
                <div class="denom-item">
                    <label class="denom-label">${valorFormateado}</label>
                    <input data-denom-id="${d.id}" data-denom-valor="${d.valor}" type="number" min="0" step="1" class="denom-input" placeholder="0" value="0">
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Monedas
    if (monedas.length > 0) {
        html += '<h4 class="denom-group">🪙 Monedas</h4>';
        html += '<div class="denom-grid">';
        monedas.forEach(d => {
            const valorFormateado = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(d.valor);
            html += `
                <div class="denom-item">
                    <label class="denom-label">${valorFormateado}</label>
                    <input data-denom-id="${d.id}" data-denom-valor="${d.valor}" type="number" min="0" step="1" class="denom-input" placeholder="0" value="0">
                </div>
            `;
        });
        html += '</div>';
    }
    
    html += '</div>';
    html += `<div class="swal-total">${totalIcon} Total ${tipoPreseleccionado === 'INGRESO' ? 'Entrada' : tipoPreseleccionado === 'EGRESO' ? 'Salida' : 'Movimiento'}<br><strong id="swal-total">$0</strong></div>`;
    html += '<textarea id="swal-desc" class="swal2-textarea" placeholder="Descripción del movimiento (opcional)" style="margin-top: 10px;"></textarea>';
    html += '<input id="swal-ref" class="swal2-input" placeholder="Referencia (opcional)" style="margin-top: 10px;">';

    const { value } = await Swal.fire({
        title: titulo,
        html: html,
        width: 800,
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
        willOpen: () => {
            const inputs = Swal.getPopup().querySelectorAll('.denom-input');
            if (inputs && inputs.length) {
                const totalEl = Swal.getPopup().querySelector('#swal-total');
                const calcular = () => {
                    let total = 0;
                    inputs.forEach(inp => {
                        const valor = parseFloat(inp.dataset.denomValor || 0);
                        const cantidad = parseInt(inp.value || 0);
                        if (!isNaN(valor) && !isNaN(cantidad) && cantidad > 0) {
                            total += valor * cantidad;
                        }
                    });
                    totalEl.textContent = new Intl.NumberFormat('es-CO', { 
                        style: 'currency', 
                        currency: 'COP',
                        minimumFractionDigits: 0
                    }).format(total);
                };
                inputs.forEach(i => {
                    i.addEventListener('input', calcular);
                    i.addEventListener('focus', function() {
                        if (this.value === '0') this.value = '';
                    });
                    i.addEventListener('blur', function() {
                        if (this.value === '') this.value = '0';
                    });
                });
                calcular();
            }
        },
        preConfirm: () => {
            const tipo_mov = document.getElementById('swal-tipo-mov').value;
            const desc = document.getElementById('swal-desc').value;
            const ref = document.getElementById('swal-ref').value;
            
            const inputs = Swal.getPopup().querySelectorAll('.denom-input');
            let monto = 0;
            let any = false;
            
            inputs.forEach(inp => {
                const cantidad = parseInt(inp.value || 0);
                if (!isNaN(cantidad) && cantidad > 0) {
                    const valor = parseFloat(inp.dataset.denomValor || 0);
                    monto += valor * cantidad;
                    any = true;
                }
            });
            
            if (!any || monto <= 0) { 
                Swal.showValidationMessage('⚠️ Ingresa al menos una cantidad para las denominaciones'); 
                return false; 
            }
            if (!tipo_mov) { 
                Swal.showValidationMessage('⚠️ Selecciona una categoría'); 
                return false; 
            }
            
            return { tipo: tipoPreseleccionado, tipo_mov, monto, desc, ref };
        }
    });

    if (!value) return;

    try{
        const token = getCookie('csrftoken');
        const payload = {
            tipo: value.tipo,
            tipo_movimiento: value.tipo_mov,
            monto: value.monto,
            descripcion: value.desc,
            referencia: value.ref
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
            Swal.fire({
                icon:'success',
                title:'✅ Registrado',
                text:data.message,
                timer:1500,
                showConfirmButton:false
            }).then(()=>{
                window.location.href = window.CAJA_URLS.dashboard;
            });
        } else {
            Swal.fire({icon:'error',title:'Error',text: data.error || 'No se pudo registrar el movimiento'});
        }
    }catch(err){
        console.error(err);
        Swal.fire({icon:'error',title:'Error',text:'Error de red al registrar movimiento'});
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
