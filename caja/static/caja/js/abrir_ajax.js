// abrir_ajax.js - maneja apertura de caja vía SweetAlert2 y AJAX

// abrir_ajax.js - maneja apertura de caja vía SweetAlert2 y AJAX

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function(){
    const btnOpen = document.getElementById('btn-open-caja');
    if (!btnOpen) return;

    btnOpen.addEventListener('click', async function(){
        // Cargar denominaciones desde servidor para construir el formulario dinámico
        let denominaciones = [];
        try {
            const respDen = await fetch(window.CAJA_URLS.denominaciones, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (respDen.ok) {
                const json = await respDen.json();
                denominaciones = (json && json.denominaciones) ? json.denominaciones : [];
            }
        } catch (e) {
            console.warn('No se pudieron cargar denominaciones, se usará campo de monto simple', e);
        }

        // Cargar información del último cierre para prellenar
        let ultimoCierre = null;
        try {
            const respCierre = await fetch(window.CAJA_URLS.ultimo_cierre, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (respCierre.ok) {
                const json = await respCierre.json();
                if (json.success && json.hay_cierre_anterior) {
                    ultimoCierre = json;
                }
            }
        } catch (e) {
            console.warn('No se pudo cargar el último cierre', e);
        }

        // Construir HTML del modal
        let html = '';
        
        // Si hay un cierre anterior, mostrar información
        if (ultimoCierre) {
            const dineroFormateado = new Intl.NumberFormat('es-CO', { 
                style: 'currency', 
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(ultimoCierre.dinero_en_caja);
            
            html += `<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; 
                            padding: 15px; 
                            border-radius: 10px; 
                            margin-bottom: 20px; 
                            text-align: center;">`;
            html += `<h3 style="margin: 0; font-size: 1rem;">💼 Dinero del Cierre Anterior</h3>`;
            html += `<p style="margin: 8px 0 0 0; font-size: 1.5rem; font-weight: bold;">${dineroFormateado}</p>`;
            html += `<p style="margin: 5px 0 0 0; font-size: 0.85rem; opacity: 0.9;">Cerrado el ${ultimoCierre.fecha_cierre} por ${ultimoCierre.cajero}</p>`;
            html += `</div>`;
        }
        
        if (denominaciones && denominaciones.length > 0) {
            // Separar y ordenar billetes y monedas
            const billetes = denominaciones.filter(d => d.tipo.toUpperCase() === 'BILLETE').sort((a, b) => b.valor - a.valor);
            const monedas = denominaciones.filter(d => d.tipo.toUpperCase() === 'MONEDA').sort((a, b) => b.valor - a.valor);

            html += '<div class="denominaciones-container" style="text-align: left;">';
            
            // Billetes
            if (billetes.length > 0) {
                html += '<h4 class="denom-group">💵 Billetes</h4>';
                html += '<div class="denom-grid">';
                billetes.forEach(d => {
                    const valorFormateado = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(d.valor);
                    // Obtener cantidad del último cierre si existe
                    const cantidadInicial = (ultimoCierre && ultimoCierre.conteos && ultimoCierre.conteos[d.id]) ? ultimoCierre.conteos[d.id] : 0;
                    html += `
                        <div class="denom-item">
                            <label class="denom-label">${valorFormateado}</label>
                            <input data-denom-id="${d.id}" 
                                   data-denom-valor="${d.valor}" 
                                   type="number" 
                                   min="0" 
                                   step="1" 
                                   class="denom-input" 
                                   placeholder="0" 
                                   value="${cantidadInicial}">
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
                    // Obtener cantidad del último cierre si existe
                    const cantidadInicial = (ultimoCierre && ultimoCierre.conteos && ultimoCierre.conteos[d.id]) ? ultimoCierre.conteos[d.id] : 0;
                    html += `
                        <div class="denom-item">
                            <label class="denom-label">${valorFormateado}</label>
                            <input data-denom-id="${d.id}" 
                                   data-denom-valor="${d.valor}" 
                                   type="number" 
                                   min="0" 
                                   step="1" 
                                   class="denom-input" 
                                   placeholder="0" 
                                   value="${cantidadInicial}">
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            html += '</div>';
            html += '<div class="swal-total">💰 Total a Abrir<br><strong id="swal-total">$0</strong></div>';
            html += '<textarea id="swal-observaciones" class="swal2-textarea" placeholder="Observaciones (opcional)" style="margin-top: 10px;"></textarea>';
        } else {
            // Fallback simple input si no hay denominaciones
            html += '<input id="swal-monto" class="swal2-input" placeholder="Monto inicial (ej. 100000)" type="number">';
            html += '<textarea id="swal-observaciones" class="swal2-textarea" placeholder="Observaciones (opcional)"></textarea>';
        }

        const { value: formValues } = await Swal.fire({
            title: '💼 Abrir Caja',
            html: html,
            width: 800,
            padding: '20px',
            focusConfirm: false,
            showCancelButton: true,
            confirmButtonText: '✅ Abrir Caja',
            cancelButtonText: '❌ Cancelar',
            confirmButtonColor: '#4CAF50',
            cancelButtonColor: '#dc3545',
            customClass: {
                container: 'caja-modal-container',
                popup: 'caja-modal-popup'
            },
            willOpen: () => {
                // Si hay inputs de denominaciones, enganchar eventos para cálculo en vivo
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
                    calcular(); // Calcular inicial
                }
            },
            preConfirm: () => {
                const obs = Swal.getPopup().querySelector('#swal-observaciones') ? Swal.getPopup().querySelector('#swal-observaciones').value : '';
                if (denominaciones && denominaciones.length > 0) {
                    // recolectar conteos
                    const inputs = Swal.getPopup().querySelectorAll('.denom-input');
                    const conteos = {};
                    let any = false;
                    inputs.forEach(inp => {
                        const cantidad = parseInt(inp.value || 0);
                        if (!isNaN(cantidad) && cantidad > 0) {
                            conteos[inp.dataset.denomId] = cantidad;
                            any = true;
                        }
                    });
                    if (!any) {
                        Swal.showValidationMessage('⚠️ Ingresa al menos una cantidad para las denominaciones');
                        return false;
                    }
                    return { conteos: conteos, observaciones: obs };
                } else {
                    const monto = Swal.getPopup().querySelector('#swal-monto').value;
                    if (!monto || Number(monto) < 0) {
                        Swal.showValidationMessage('⚠️ Ingresa un monto válido');
                        return false;
                    }
                    return { monto: monto, observaciones: obs };
                }
            }
        });

        if (!formValues) return; // cancelado

        // Enviar petición AJAX
        try {
            const token = getCookie('csrftoken');
            const payload = {};
            if (formValues.conteos) payload.conteos = formValues.conteos;
            if (formValues.monto) payload.monto_inicial = formValues.monto;
            if (formValues.observaciones) payload.observaciones = formValues.observaciones;

            const resp = await fetch(window.CAJA_URLS.abrir, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();
            if (resp.ok && data.success){
                Swal.fire({
                    icon: 'success',
                    title: 'Caja abierta',
                    html: `<p>${data.message}</p>`,
                    timer: 1600,
                    showConfirmButton: false
                }).then(()=>{
                    // recargar la página para mostrar la caja abierta
                    window.location.href = window.CAJA_URLS.dashboard;
                });
            } else {
                Swal.fire({icon:'error',title:'Error',text: data.error || 'No se pudo abrir la caja'});
            }
        } catch (err) {
            console.error(err);
            Swal.fire({icon:'error',title:'Error',text: 'Error de red al intentar abrir la caja'});
        }
    });
});
