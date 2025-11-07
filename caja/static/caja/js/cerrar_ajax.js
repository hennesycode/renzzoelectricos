// cerrar_ajax.js - modal de cierre con conteo de denominaciones y envío AJAX

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

async function fetchDenominaciones(){
    const resp = await fetch(window.CAJA_URLS.denominaciones);
    const data = await resp.json();
    if (resp.ok && data.success) return data.denominaciones;
    return [];
}

async function fetchEstadoCaja(){
    const resp = await fetch(window.CAJA_URLS.estado_caja);
    const data = await resp.json();
    if (resp.ok && data.success) return data;
    return null;
}

const formatearMoneda = (valor) => {
    return new Intl.NumberFormat('es-CO', { 
        style: 'currency', 
        currency: 'COP',
        minimumFractionDigits: 0
    }).format(valor);
};

const limpiarNumero = (texto) => {
    if (!texto || texto === '') return '0';
    return texto.toString().replace(/[^\d]/g, '');
};

async function openCerrarModal(){
    // Cargar denominaciones y estado de la caja
    const denoms = await fetchDenominaciones();
    const estadoCaja = await fetchEstadoCaja();
    
    if (!estadoCaja) {
        Swal.fire({icon: 'error', title: 'Error', text: 'No se pudo obtener el estado de la caja'});
        return;
    }
    
    const totalDisponible = estadoCaja.total_disponible;
    const totalEntradasBanco = estadoCaja.total_entradas_banco || 0;
    
    // Debe Haber en Caja = Total Disponible (ya excluye entradas banco)
    const debeHaberEnCaja = totalDisponible;
    
    // Separar y ordenar billetes y monedas
    const billetes = denoms.filter(d => d.tipo.toUpperCase() === 'BILLETE').sort((a, b) => b.valor - a.valor);
    const monedas = denoms.filter(d => d.tipo.toUpperCase() === 'MONEDA').sort((a, b) => b.valor - a.valor);

    let html = '<div class="denominaciones-container" style="text-align: left;">';
    
    // 1. Mostrar "Debe Haber en Caja" (total teórico SIN incluir entradas banco)
    const debeHaberFormateado = formatearMoneda(debeHaberEnCaja);
    
    html += `<div style="background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); 
                        color: white; 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 15px; 
                        text-align: center;
                        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.3);">`;
    html += `<h3 style="margin: 0; font-size: 1.2rem;">💰 Debe Haber en Caja</h3>`;
    html += `<p style="margin: 10px 0 5px 0; font-size: 1.8rem; font-weight: bold;">${debeHaberFormateado}</p>`;
    html += `<p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">(Entradas banco no incluidas)</p>`;
    html += `</div>`;
    
    // 2. Nueva sección: "¿Cuánto hay en Caja?" - Color verde
    html += `<div style="background: linear-gradient(135deg, #43a047 0%, #66bb6a 100%); 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 15px;
                        box-shadow: 0 4px 10px rgba(67, 160, 71, 0.3);">`;
    html += `<label style="display: block; font-weight: 700; margin-bottom: 10px; color: white; font-size: 1.1rem; text-align: center;">¿Cuánto hay en Caja?</label>`;
    html += `<input id="swal-cuanto-hay" type="text" class="form-control-modern" placeholder="$ 0" value="" style="width: 100%; padding: 14px; border-radius: 8px; border: 3px solid white; font-size: 22px; font-weight: 700; text-align: center; background: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">`;
    html += `</div>`;
    
    // 3. Sección de diferencia (inicialmente oculta)
    html += `<div id="swal-diferencia-cuadre" style="display: none; margin-bottom: 15px; padding: 12px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 15px;"></div>`;
    // 3. Sección de diferencia (inicialmente oculta)
    html += `<div id="swal-diferencia-cuadre" style="display: none; margin-bottom: 15px; padding: 12px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 15px;"></div>`;
    
    // 4. Distribución del Dinero (usando "Cuánto hay" como base)
    html += '<div style="margin-top: 20px; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px; border: 2px solid #e0e0e0;">';
    html += '<h4 style="margin: 0 0 15px 0; color: #2c3e50; font-weight: 700; text-align: center;">📦 Distribución del Dinero</h4>';
    
    html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">';
    // Dinero en caja
    html += '<div>';
    html += '<label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2c3e50; font-size: 14px;">💵 Dinero en Caja</label>';
    html += '<input id="swal-dinero-caja" type="text" class="form-control-modern" placeholder="$ 0" value="$ 0" style="width: 100%; padding: 12px; border-radius: 8px; border: 2px solid #e0e0e0; font-size: 18px; font-weight: 600; text-align: center; background: white;">';
    html += '</div>';
    
    // Dinero guardado
    html += '<div>';
    html += '<label style="display: block; font-weight: 600; margin-bottom: 8px; color: #2c3e50; font-size: 14px;">🔒 Dinero Guardado (Fuera de Caja)</label>';
    html += '<input id="swal-dinero-guardado" type="text" class="form-control-modern" placeholder="$ 0" value="$ 0" style="width: 100%; padding: 12px; border-radius: 8px; border: 2px solid #e0e0e0; font-size: 18px; font-weight: 600; text-align: center; background: white;">';
    html += '</div>';
    html += '</div>';
    
    // Suma total y validación
    html += '<div style="background: white; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid #3498db;">';
    html += '<strong style="color: #2c3e50; font-size: 15px;">Suma: </strong>';
    html += '<strong id="swal-suma-distribucion" style="color: #3498db; font-size: 20px; font-weight: 700;">$0</strong>';
    html += '</div>';
    
    // Mensaje de error/validación distribución
    html += '<div id="swal-error-distribucion" style="display: none; margin-top: 10px; padding: 10px; border-radius: 8px; background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; text-align: center; font-weight: 600;"></div>';
    html += '</div>'; // Fin distribución
    
    // 5. Nueva sección: Distribución de Caja (conteo de billetes/monedas del dinero EN CAJA)
    html += '<div style="margin-top: 20px; padding: 20px; background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); border-radius: 12px; border: 2px solid #f0a07c;">';
    html += '<h4 style="margin: 0 0 15px 0; color: #2c3e50; font-weight: 700; text-align: center;">🏦 Distribución de Caja</h4>';
    html += '<p style="text-align: center; color: #555; margin-bottom: 15px; font-size: 14px;">Ingresa exactamente los billetes y monedas que quedaron en caja</p>';
    
    // Billetes
    if (billetes.length > 0) {
        html += '<h5 class="denom-group">💵 Billetes</h5>';
        html += '<div class="denom-grid">';
        billetes.forEach(d => {
            const valorFormateado = formatearMoneda(d.valor);
            
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
                           value="0">
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Monedas
    if (monedas.length > 0) {
        html += '<h5 class="denom-group">🪙 Monedas</h5>';
        html += '<div class="denom-grid">';
        monedas.forEach(d => {
            const valorFormateado = formatearMoneda(d.valor);
            
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
                           value="0">
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Total contado y validación
    html += '<div style="margin-top: 15px; background: white; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid #28a745;">';
    html += '<strong style="color: #2c3e50; font-size: 15px;">💰 Total Contado: </strong>';
    html += '<strong id="swal-total-contado" style="color: #28a745; font-size: 20px; font-weight: 700;">$0</strong>';
    html += '</div>';
    
    // Mensaje de validación del conteo
    html += '<div id="swal-error-conteo" style="display: none; margin-top: 10px; padding: 10px; border-radius: 8px; text-align: center; font-weight: 600;"></div>';
    html += '</div>'; // Fin distribución de caja
    
    // Observaciones
    html += '<textarea id="swal-observaciones" class="swal2-textarea" placeholder="Observaciones (opcional)" style="margin-top: 15px;"></textarea>';
    html += '</div>'; // Fin container

    const { value: result } = await Swal.fire({
        title: '🔒 Cerrar Caja',
        html: html,
        width: 900,
        padding: '20px',
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: '✅ Cerrar Caja',
        cancelButtonText: '❌ Cancelar',
        confirmButtonColor: '#e57373',
        cancelButtonColor: '#6c757d',
        customClass: {
            container: 'caja-modal-container',
            popup: 'caja-modal-popup'
        },
        willOpen: () => {
            const popup = Swal.getPopup();
            
            // Elementos del DOM
            const cuantoHayInput = popup.querySelector('#swal-cuanto-hay');
            const diferenciaCuadreEl = popup.querySelector('#swal-diferencia-cuadre');
            const dineroCajaInput = popup.querySelector('#swal-dinero-caja');
            const dineroGuardadoInput = popup.querySelector('#swal-dinero-guardado');
            const sumaDistribucionEl = popup.querySelector('#swal-suma-distribucion');
            const errorDistribucionEl = popup.querySelector('#swal-error-distribucion');
            const denomInputs = popup.querySelectorAll('.denom-input');
            const totalContadoEl = popup.querySelector('#swal-total-contado');
            const errorConteoEl = popup.querySelector('#swal-error-conteo');
            
            // Función para formatear inputs de dinero
            const formatearInput = (input) => {
                input.addEventListener('input', function() {
                    let value = limpiarNumero(this.value);
                    if (value && value !== '0') {
                        value = parseInt(value).toLocaleString('es-CO');
                        this.value = `$ ${value}`;
                    } else {
                        this.value = '';
                    }
                    recalcularTodo();
                });
                
                input.addEventListener('focus', function() {
                    if (this.value === '$ 0' || this.value === '$ ' || this.value === '') {
                        this.value = '';
                    }
                    this.select();
                });
                
                input.addEventListener('blur', function() {
                    if (this.value === '' || this.value === '$ ') {
                        this.value = '$ 0';
                    }
                });
            };
            
            // Función para calcular el total contado de denominaciones
            const calcularTotalContado = () => {
                let total = 0;
                denomInputs.forEach(inp => {
                    const valor = parseFloat(inp.dataset.denomValor || 0);
                    const cantidad = parseInt(inp.value || 0);
                    if (!isNaN(valor) && !isNaN(cantidad) && cantidad > 0) {
                        total += valor * cantidad;
                    }
                });
                return total;
            };
            
            // Función principal que recalcula todo
            const recalcularTodo = () => {
                // 1. Validar "Cuánto hay" vs "Debe Haber en Caja" (sin entradas banco)
                const cuantoHayLimpio = limpiarNumero(cuantoHayInput.value || '0');
                const cuantoHay = parseFloat(cuantoHayLimpio) || 0;
                
                if (cuantoHay > 0) {
                    const diferencia = cuantoHay - debeHaberEnCaja;
                    
                    if (Math.abs(diferencia) < 0.01) {
                        // Sin diferencias
                        diferenciaCuadreEl.style.display = 'block';
                        diferenciaCuadreEl.style.background = '#d4edda';
                        diferenciaCuadreEl.style.color = '#155724';
                        diferenciaCuadreEl.style.border = '2px solid #c3e6cb';
                        diferenciaCuadreEl.innerHTML = '✅ Sin diferencias - Cuadre perfecto';
                    } else if (diferencia > 0) {
                        // Sobrante
                        const diferenciaFormateada = formatearMoneda(Math.abs(diferencia));
                        diferenciaCuadreEl.style.display = 'block';
                        diferenciaCuadreEl.style.background = '#d4edda';
                        diferenciaCuadreEl.style.color = '#155724';
                        diferenciaCuadreEl.style.border = '2px solid #c3e6cb';
                        diferenciaCuadreEl.innerHTML = `✅ <strong>Sobrante:</strong> ${diferenciaFormateada}`;
                    } else {
                        // Faltante
                        const diferenciaFormateada = formatearMoneda(Math.abs(diferencia));
                        diferenciaCuadreEl.style.display = 'block';
                        diferenciaCuadreEl.style.background = '#f8d7da';
                        diferenciaCuadreEl.style.color = '#721c24';
                        diferenciaCuadreEl.style.border = '2px solid #f5c6cb';
                        diferenciaCuadreEl.innerHTML = `⚠️ <strong>Faltante:</strong> ${diferenciaFormateada}`;
                    }
                } else {
                    diferenciaCuadreEl.style.display = 'none';
                }
                
                // 2. Validar distribución (Dinero en Caja + Dinero Guardado)
                const dineroCajaLimpio = limpiarNumero(dineroCajaInput.value || '0');
                const dineroGuardadoLimpio = limpiarNumero(dineroGuardadoInput.value || '0');
                
                const dineroCaja = parseFloat(dineroCajaLimpio) || 0;
                const dineroGuardado = parseFloat(dineroGuardadoLimpio) || 0;
                const sumaDistribucion = dineroCaja + dineroGuardado;
                
                sumaDistribucionEl.textContent = formatearMoneda(sumaDistribucion);
                
                // Validar que no supere "Cuánto hay"
                if (cuantoHay > 0 && sumaDistribucion > cuantoHay + 0.01) {
                    errorDistribucionEl.style.display = 'block';
                    errorDistribucionEl.innerHTML = `❌ La suma (${formatearMoneda(sumaDistribucion)}) no puede ser mayor a "Cuánto hay" (${formatearMoneda(cuantoHay)})`;
                } else if (cuantoHay > 0 && Math.abs(sumaDistribucion - cuantoHay) > 0.01) {
                    errorDistribucionEl.style.display = 'block';
                    errorDistribucionEl.innerHTML = `⚠️ La suma (${formatearMoneda(sumaDistribucion)}) debe ser igual a "Cuánto hay" (${formatearMoneda(cuantoHay)})`;
                } else if (dineroCaja === 0 && dineroGuardado === 0 && cuantoHay > 0) {
                    errorDistribucionEl.style.display = 'block';
                    errorDistribucionEl.innerHTML = '⚠️ Debes distribuir el dinero entre Caja y Guardado';
                } else {
                    errorDistribucionEl.style.display = 'none';
                }
                
                // 3. Validar conteo de denominaciones vs Dinero en Caja
                const totalContado = calcularTotalContado();
                totalContadoEl.textContent = formatearMoneda(totalContado);
                
                if (dineroCaja > 0) {
                    if (Math.abs(totalContado - dineroCaja) < 0.01) {
                        // Coincide perfectamente
                        errorConteoEl.style.display = 'block';
                        errorConteoEl.style.background = '#d4edda';
                        errorConteoEl.style.color = '#155724';
                        errorConteoEl.style.border = '2px solid #c3e6cb';
                        errorConteoEl.innerHTML = '✅ El conteo coincide con el Dinero en Caja';
                    } else if (totalContado > dineroCaja) {
                        // Hay más contado que declarado
                        const diferencia = totalContado - dineroCaja;
                        errorConteoEl.style.display = 'block';
                        errorConteoEl.style.background = '#fff3cd';
                        errorConteoEl.style.color = '#856404';
                        errorConteoEl.style.border = '2px solid #ffeaa7';
                        errorConteoEl.innerHTML = `⚠️ Contaste ${formatearMoneda(diferencia)} más de lo declarado en "Dinero en Caja"`;
                    } else {
                        // Hay menos contado que declarado
                        const diferencia = dineroCaja - totalContado;
                        errorConteoEl.style.display = 'block';
                        errorConteoEl.style.background = '#f8d7da';
                        errorConteoEl.style.color = '#721c24';
                        errorConteoEl.style.border = '2px solid #f5c6cb';
                        errorConteoEl.innerHTML = `❌ Contaste ${formatearMoneda(diferencia)} menos de lo declarado en "Dinero en Caja"`;
                    }
                } else {
                    errorConteoEl.style.display = 'none';
                }
            };
            
            // Aplicar formateo a los inputs de dinero
            formatearInput(cuantoHayInput);
            formatearInput(dineroCajaInput);
            formatearInput(dineroGuardadoInput);
            
            // Listeners para denominaciones
            denomInputs.forEach(inp => {
                inp.addEventListener('input', recalcularTodo);
                inp.addEventListener('focus', function() {
                    if (this.value === '0') this.value = '';
                });
                inp.addEventListener('blur', function() {
                    if (this.value === '') this.value = '0';
                });
            });
            
            // Calcular inicial
            recalcularTodo();
        },
        preConfirm: () => {
            const popup = Swal.getPopup();
            const cuantoHayInput = popup.querySelector('#swal-cuanto-hay');
            const dineroCajaInput = popup.querySelector('#swal-dinero-caja');
            const dineroGuardadoInput = popup.querySelector('#swal-dinero-guardado');
            const denomInputs = popup.querySelectorAll('.denom-input');
            const obs = popup.querySelector('#swal-observaciones') ? popup.querySelector('#swal-observaciones').value : '';
            
            // 1. Validar que "Cuánto hay" tenga valor
            const cuantoHayLimpio = limpiarNumero(cuantoHayInput.value || '0');
            const cuantoHay = parseFloat(cuantoHayLimpio) || 0;
            
            if (cuantoHay <= 0) {
                Swal.showValidationMessage('⚠️ Debes ingresar el valor de "¿Cuánto hay?"');
                return false;
            }
            
            // 2. Validar distribución del dinero
            const dineroCajaLimpio = limpiarNumero(dineroCajaInput.value || '0');
            const dineroGuardadoLimpio = limpiarNumero(dineroGuardadoInput.value || '0');
            
            const dineroCaja = parseFloat(dineroCajaLimpio) || 0;
            const dineroGuardado = parseFloat(dineroGuardadoLimpio) || 0;
            const sumaDistribucion = dineroCaja + dineroGuardado;
            
            if (dineroCaja === 0 && dineroGuardado === 0) {
                Swal.showValidationMessage('⚠️ Debes distribuir el dinero entre Caja y Guardado');
                return false;
            }
            
            if (Math.abs(sumaDistribucion - cuantoHay) > 0.01) {
                Swal.showValidationMessage(`❌ La distribución (${formatearMoneda(sumaDistribucion)}) debe ser igual a "Cuánto hay" (${formatearMoneda(cuantoHay)})`);
                return false;
            }
            
            // 3. Validar conteo de denominaciones
            const conteos = {};
            let totalContado = 0;
            let hayConteo = false;
            
            denomInputs.forEach(inp => {
                const cantidad = parseInt(inp.value || 0);
                if (!isNaN(cantidad) && cantidad > 0) {
                    conteos[inp.dataset.denomId] = cantidad;
                    const valor = parseFloat(inp.dataset.denomValor || 0);
                    totalContado += valor * cantidad;
                    hayConteo = true;
                }
            });
            
            // Solo si hay dinero en caja, debe haber conteo
            if (dineroCaja > 0 && !hayConteo) {
                Swal.showValidationMessage('⚠️ Debes contar las denominaciones del dinero que queda en caja');
                return false;
            }
            
            // El total contado debe coincidir con el dinero en caja
            if (dineroCaja > 0 && Math.abs(totalContado - dineroCaja) > 0.01) {
                Swal.showValidationMessage(`❌ El Total Contado (${formatearMoneda(totalContado)}) debe ser igual al Dinero en Caja (${formatearMoneda(dineroCaja)})`);
                return false;
            }
            
            return {
                cuanto_hay: cuantoHay,
                dinero_en_caja: dineroCaja,
                dinero_guardado: dineroGuardado,
                conteos: conteos,
                observaciones: obs
            };
        }
    });

    if (!result) return; // cancel

    // Enviar cierre via AJAX
    try{
        const token = getCookie('csrftoken');
        const payload = { 
            cuanto_hay: result.cuanto_hay,
            monto_declarado: result.cuanto_hay, // El "cuanto_hay" es el monto real declarado
            observaciones: result.observaciones, 
            conteos: result.conteos,
            dinero_en_caja: result.dinero_en_caja,
            dinero_guardado: result.dinero_guardado
        };
        
        const resp = await fetch(window.CAJA_URLS.cerrar, {
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
            const diferencia = data.diferencia;
            const icon = diferencia === 0 ? 'success' : 'warning';
            const title = diferencia === 0 ? 'Caja cerrada sin diferencias' : 'Caja cerrada con diferencias';
            const diferenciaFormateada = new Intl.NumberFormat('es-CO', { 
                style: 'currency', 
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(Math.abs(diferencia));
            
            let mensaje = `<p><strong>💵 Total Contado (Declarado):</strong> ${new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(data.monto_final_declarado)}</p>`;
            mensaje += `<p><strong>📊 Total Esperado (Sistema):</strong> ${new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(data.monto_final_sistema)}</p>`;
            mensaje += '<hr style="margin: 15px 0; border-top: 2px solid #ddd;">';
            
            if (diferencia > 0) {
                mensaje += `<p style="font-size: 1.2rem; margin-top: 15px;" class="text-success"><strong>✅ Sobrante:</strong> ${diferenciaFormateada}</p>`;
                mensaje += `<p style="color: #666; font-size: 0.9rem; margin-top: 5px;">Hay más dinero del esperado</p>`;
            } else if (diferencia < 0) {
                mensaje += `<p style="font-size: 1.2rem; margin-top: 15px;" class="text-danger"><strong>⚠️ Faltante:</strong> ${diferenciaFormateada}</p>`;
                mensaje += `<p style="color: #666; font-size: 0.9rem; margin-top: 5px;">Hay menos dinero del esperado</p>`;
            } else {
                mensaje += `<p style="font-size: 1.2rem; margin-top: 15px;" class="text-success"><strong>✓ Cuadre Perfecto</strong></p>`;
                mensaje += `<p style="color: #666; font-size: 0.9rem; margin-top: 5px;">No hay diferencias</p>`;
            }
            
            Swal.fire({
                icon: icon,
                title: title,
                html: mensaje,
                showConfirmButton: true,
                confirmButtonText: 'OK'
            }).then(()=>{
                window.location.href = window.CAJA_URLS.dashboard;
            });
        } else {
            Swal.fire({icon:'error',title:'Error',text: data.error || 'No se pudo cerrar la caja'});
        }
    }catch(err){
        console.error(err);
        Swal.fire({icon:'error',title:'Error',text:'Error de red al cerrar la caja'});
    }
}

// Attach handler
document.addEventListener('DOMContentLoaded', function(){
    const btnClose = document.getElementById('btn-close-caja');
    if (btnClose) btnClose.addEventListener('click', openCerrarModal);
});
