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

async function openCerrarModal(){
    // Cargar denominaciones y estado de la caja
    const denoms = await fetchDenominaciones();
    const estadoCaja = await fetchEstadoCaja();
    
    if (!estadoCaja) {
        Swal.fire({icon: 'error', title: 'Error', text: 'No se pudo obtener el estado de la caja'});
        return;
    }
    
    const totalDisponible = estadoCaja.total_disponible;
    const denominacionesEsperadas = estadoCaja.denominaciones_esperadas || {};
    
    // Separar y ordenar billetes y monedas
    const billetes = denoms.filter(d => d.tipo.toUpperCase() === 'BILLETE').sort((a, b) => b.valor - a.valor);
    const monedas = denoms.filter(d => d.tipo.toUpperCase() === 'MONEDA').sort((a, b) => b.valor - a.valor);

    let html = '<div class="denominaciones-container" style="text-align: left;">';
    
    // Mostrar total disponible al inicio
    const totalDisponibleFormateado = new Intl.NumberFormat('es-CO', { 
        style: 'currency', 
        currency: 'COP', 
        minimumFractionDigits: 0 
    }).format(totalDisponible);
    
    html += `<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 20px; 
                        text-align: center;">`;
    html += `<h3 style="margin: 0; font-size: 1.2rem;">💰 Debe Haber</h3>`;
    html += `<p style="margin: 10px 0 0 0; font-size: 1.8rem; font-weight: bold;">${totalDisponibleFormateado}</p>`;
    html += `</div>`;
    
    // Billetes
    if (billetes.length > 0) {
        html += '<h4 class="denom-group">💵 Billetes</h4>';
        html += '<div class="denom-grid">';
        billetes.forEach(d => {
            const valorFormateado = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(d.valor);
            const esperado = denominacionesEsperadas[d.id] || 0;
            const labelEsperado = esperado > 0 ? `<small style="color: #666; display: block; margin-top: 4px;">Esperado: ${esperado}</small>` : '';
            
            html += `
                <div class="denom-item">
                    <label class="denom-label">
                        ${valorFormateado}
                        ${labelEsperado}
                    </label>
                    <input data-denom-id="${d.id}" 
                           data-denom-valor="${d.valor}" 
                           data-esperado="${esperado}"
                           type="number" 
                           min="0" 
                           step="1" 
                           class="denom-input" 
                           placeholder="${esperado}" 
                           value="${esperado}">
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
            const esperado = denominacionesEsperadas[d.id] || 0;
            const labelEsperado = esperado > 0 ? `<small style="color: #666; display: block; margin-top: 4px;">Esperado: ${esperado}</small>` : '';
            
            html += `
                <div class="denom-item">
                    <label class="denom-label">
                        ${valorFormateado}
                        ${labelEsperado}
                    </label>
                    <input data-denom-id="${d.id}" 
                           data-denom-valor="${d.valor}"
                           data-esperado="${esperado}"
                           type="number" 
                           min="0" 
                           step="1" 
                           class="denom-input" 
                           placeholder="${esperado}" 
                           value="${esperado}">
                </div>
            `;
        });
        html += '</div>';
    }
    
    html += '</div>';
    html += '<div class="swal-total">💰 Total Contado<br><strong id="swal-total">$0</strong></div>';
    html += '<div id="swal-diferencia" class="swal-diferencia" style="display: none; margin-top: 10px; padding: 10px; border-radius: 5px;"></div>';
    
    // Nuevos campos: Dinero en caja y dinero guardado
    html += '<div style="margin-top: 25px; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px; border: 2px solid #e0e0e0;">';
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
    
    // Mensaje de error/validación
    html += '<div id="swal-error-distribucion" style="display: none; margin-top: 10px; padding: 10px; border-radius: 8px; background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; text-align: center; font-weight: 600;"></div>';
    html += '</div>';
    
    html += '<textarea id="swal-observaciones" class="swal2-textarea" placeholder="Observaciones (opcional)" style="margin-top: 15px;"></textarea>';

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
            const inputs = Swal.getPopup().querySelectorAll('.denom-input');
            if (inputs && inputs.length) {
                const totalEl = Swal.getPopup().querySelector('#swal-total');
                const diferenciaEl = Swal.getPopup().querySelector('#swal-diferencia');
                const dineroCajaInput = Swal.getPopup().querySelector('#swal-dinero-caja');
                const dineroGuardadoInput = Swal.getPopup().querySelector('#swal-dinero-guardado');
                const sumaDistribucionEl = Swal.getPopup().querySelector('#swal-suma-distribucion');
                const errorDistribucionEl = Swal.getPopup().querySelector('#swal-error-distribucion');
                
                const formatearMoneda = (valor) => {
                    return new Intl.NumberFormat('es-CO', { 
                        style: 'currency', 
                        currency: 'COP',
                        minimumFractionDigits: 0
                    }).format(valor);
                };
                
                const limpiarNumero = (texto) => {
                    return texto.replace(/[^\d]/g, '');
                };
                
                // Variable para rastrear si el usuario ha modificado los campos de distribución
                let distribucionModificada = false;
                
                const calcular = () => {
                    let total = 0;
                    inputs.forEach(inp => {
                        const valor = parseFloat(inp.dataset.denomValor || 0);
                        const cantidad = parseInt(inp.value || 0);
                        if (!isNaN(valor) && !isNaN(cantidad) && cantidad > 0) {
                            total += valor * cantidad;
                        }
                    });
                    
                    totalEl.textContent = formatearMoneda(total);
                    
                    // Auto-llenar "Dinero en Caja" con el total si no se ha modificado
                    if (!distribucionModificada && total > 0) {
                        // Formatear el total de la misma forma que los inputs esperan
                        const totalFormateado = parseInt(total).toLocaleString('es-CO');
                        dineroCajaInput.value = `$ ${totalFormateado}`;
                        dineroGuardadoInput.value = '$ 0';
                    }
                    
                    // Calcular y mostrar diferencia
                    const diferencia = total - totalDisponible;
                    
                    if (Math.abs(diferencia) > 0.01) {
                        const diferenciaFormateada = formatearMoneda(Math.abs(diferencia));
                        
                        if (diferencia > 0) {
                            diferenciaEl.style.display = 'block';
                            diferenciaEl.style.background = '#d4edda';
                            diferenciaEl.style.color = '#155724';
                            diferenciaEl.style.border = '1px solid #c3e6cb';
                            diferenciaEl.innerHTML = `✅ <strong>Sobrante:</strong> ${diferenciaFormateada}`;
                        } else {
                            diferenciaEl.style.display = 'block';
                            diferenciaEl.style.background = '#f8d7da';
                            diferenciaEl.style.color = '#721c24';
                            diferenciaEl.style.border = '1px solid #f5c6cb';
                            diferenciaEl.innerHTML = `⚠️ <strong>Faltante:</strong> ${diferenciaFormateada}`;
                        }
                    } else {
                        diferenciaEl.style.display = 'block';
                        diferenciaEl.style.background = '#d4edda';
                        diferenciaEl.style.color = '#155724';
                        diferenciaEl.style.border = '1px solid #c3e6cb';
                        diferenciaEl.innerHTML = `✅ <strong>Sin diferencias</strong> - Cuadre perfecto`;
                    }
                    
                    // Validar distribución
                    validarDistribucion(total);
                };
                
                const validarDistribucion = (totalContado) => {
                    const dineroCajaLimpio = limpiarNumero(dineroCajaInput.value || '0');
                    const dineroGuardadoLimpio = limpiarNumero(dineroGuardadoInput.value || '0');
                    
                    const dineroCaja = parseFloat(dineroCajaLimpio) || 0;
                    const dineroGuardado = parseFloat(dineroGuardadoLimpio) || 0;
                    const suma = dineroCaja + dineroGuardado;
                    
                    sumaDistribucionEl.textContent = formatearMoneda(suma);
                    
                    // Validaciones
                    if (dineroCaja === 0 && dineroGuardado === 0) {
                        errorDistribucionEl.style.display = 'block';
                        errorDistribucionEl.innerHTML = '⚠️ Al menos uno de los campos debe tener un valor mayor a cero';
                        errorDistribucionEl.style.background = '#f8d7da';
                        return false;
                    } else if (Math.abs(suma - totalContado) > 0.01) {
                        errorDistribucionEl.style.display = 'block';
                        errorDistribucionEl.innerHTML = `❌ La suma (${formatearMoneda(suma)}) no coincide con el Total Contado (${formatearMoneda(totalContado)})`;
                        errorDistribucionEl.style.background = '#f8d7da';
                        return false;
                    } else {
                        errorDistribucionEl.style.display = 'none';
                        return true;
                    }
                };
                
                // Formatear inputs de dinero mientras se escribe
                const formatearInput = (input) => {
                    input.addEventListener('input', function() {
                        distribucionModificada = true; // Marcar como modificado
                        let value = limpiarNumero(this.value);
                        if (value) {
                            value = parseInt(value).toLocaleString('es-CO');
                            this.value = `$ ${value}`;
                        } else {
                            this.value = '';
                        }
                        calcular(); // Recalcular al cambiar distribución
                    });
                    
                    input.addEventListener('focus', function() {
                        distribucionModificada = true; // Marcar como modificado al hacer focus
                        if (this.value === '$ 0' || this.value === '$ ') {
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
                
                formatearInput(dineroCajaInput);
                formatearInput(dineroGuardadoInput);
                
                inputs.forEach(i => {
                    i.addEventListener('input', calcular);
                    i.addEventListener('focus', function() {
                        if (this.value === '0') this.value = '';
                    });
                    i.addEventListener('blur', function() {
                        if (this.value === '') {
                            const esperado = this.dataset.esperado || '0';
                            this.value = esperado;
                        }
                    });
                });
                
                calcular(); // Calcular inicial con valores esperados
            }
        },
        preConfirm: () => {
            const obs = Swal.getPopup().querySelector('#swal-observaciones') ? Swal.getPopup().querySelector('#swal-observaciones').value : '';
            const inputs = Swal.getPopup().querySelectorAll('.denom-input');
            const dineroCajaInput = Swal.getPopup().querySelector('#swal-dinero-caja');
            const dineroGuardadoInput = Swal.getPopup().querySelector('#swal-dinero-guardado');
            
            const conteos = {};
            let total = 0;
            let any = false;
            
            inputs.forEach(inp => {
                const cantidad = parseInt(inp.value || 0);
                if (!isNaN(cantidad) && cantidad > 0) {
                    conteos[inp.dataset.denomId] = cantidad;
                    const valor = parseFloat(inp.dataset.denomValor || 0);
                    total += valor * cantidad;
                    any = true;
                }
            });
            
            if (!any) {
                Swal.showValidationMessage('⚠️ Ingresa al menos una cantidad para las denominaciones');
                return false;
            }
            
            // Validar distribución del dinero
            const limpiarNumero = (texto) => {
                return texto.replace(/[^\d]/g, '');
            };
            
            const dineroCajaLimpio = limpiarNumero(dineroCajaInput.value || '$ 0');
            const dineroGuardadoLimpio = limpiarNumero(dineroGuardadoInput.value || '$ 0');
            
            const dineroCaja = parseFloat(dineroCajaLimpio) || 0;
            const dineroGuardado = parseFloat(dineroGuardadoLimpio) || 0;
            const sumaDistribucion = dineroCaja + dineroGuardado;
            
            // Debug: ver qué valores se están leyendo
            console.log('Debug valores:', {
                dineroCajaInput: dineroCajaInput.value,
                dineroGuardadoInput: dineroGuardadoInput.value,
                dineroCajaLimpio,
                dineroGuardadoLimpio,
                dineroCaja,
                dineroGuardado,
                sumaDistribucion,
                total
            });
            
            // Validación 1: Al menos uno debe tener valor
            if (dineroCaja === 0 && dineroGuardado === 0) {
                Swal.showValidationMessage('⚠️ Debes especificar cuánto dinero quedó en caja o cuánto se guardó fuera de la caja (al menos uno debe ser mayor a cero)');
                return false;
            }
            
            // Validación 2: La suma debe coincidir con el total contado
            if (Math.abs(sumaDistribucion - total) > 0.01) {
                const totalFormateado = new Intl.NumberFormat('es-CO', { 
                    style: 'currency', 
                    currency: 'COP',
                    minimumFractionDigits: 0
                }).format(total);
                const sumaFormateada = new Intl.NumberFormat('es-CO', { 
                    style: 'currency', 
                    currency: 'COP',
                    minimumFractionDigits: 0
                }).format(sumaDistribucion);
                
                Swal.showValidationMessage(`❌ La distribución (${sumaFormateada}) no coincide con el Total Contado (${totalFormateado})`);
                return false;
            }
            
            return { 
                conteos: conteos, 
                observaciones: obs, 
                total: total,
                dinero_en_caja: dineroCaja,
                dinero_guardado: dineroGuardado
            };
        }
    });

    if (!result) return; // cancel

    // Enviar cierre via AJAX
    try{
        const token = getCookie('csrftoken');
        const payload = { 
            monto_declarado: result.total, 
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
