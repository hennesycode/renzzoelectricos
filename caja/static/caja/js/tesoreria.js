/**
 * JavaScript para el módulo de Tesorería
 * Renzzo Eléctricos - Villavicencio, Meta
 */

// Variables globales
let modalEgreso;
let modalTransferencia;
let modalBalance;
let tipoEgresoActual = 'GASTO'; // 'GASTO' o 'INVERSION'

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Inicializando Tesorería...');
    
    // Inicializar modales
    const modalEgresoEl = document.getElementById('modalRegistrarEgreso');
    const modalTransferenciaEl = document.getElementById('modalTransferirFondos');
    const modalBalanceEl = document.getElementById('modalBalanceCuentas');
    
    if (modalEgresoEl) {
        modalEgreso = new bootstrap.Modal(modalEgresoEl);
    }
    
    if (modalTransferenciaEl) {
        modalTransferencia = new bootstrap.Modal(modalTransferenciaEl);
    }
    
    if (modalBalanceEl) {
        modalBalance = new bootstrap.Modal(modalBalanceEl);
    }
    
    // Event listeners para botones principales
    const btnGasto = document.getElementById('btn-registrar-gasto');
    const btnCompra = document.getElementById('btn-registrar-compra');
    const btnTransferir = document.getElementById('btn-transferir-fondos');
    
    if (btnGasto) {
        btnGasto.addEventListener('click', openModalGasto);
    }
    
    if (btnCompra) {
        btnCompra.addEventListener('click', openModalCompra);
    }
    
    if (btnTransferir) {
        btnTransferir.addEventListener('click', openModalTransferencia);
    }
    
    // Event listener para guardar egreso
    const btnGuardarEgreso = document.getElementById('btn-guardar-egreso');
    if (btnGuardarEgreso) {
        btnGuardarEgreso.addEventListener('click', registrarEgreso);
    }
    
    // Event listener para guardar transferencia
    const btnGuardarTransferencia = document.getElementById('btn-guardar-transferencia');
    if (btnGuardarTransferencia) {
        btnGuardarTransferencia.addEventListener('click', realizarTransferencia);
    }
    
    // Event listener para guardar balance
    const btnGuardarBalance = document.getElementById('btn-guardar-balance');
    if (btnGuardarBalance) {
        btnGuardarBalance.addEventListener('click', aplicarBalance);
    }
    
    // Formatear inputs de monto
    setupMontoInput('monto-egreso');
    setupMontoInput('monto-transferencia');
    
    // Configurar inputs de balance
    setupBalanceInputs();
    
    // Event listener para tecla B (abrir modal de balance)
    document.addEventListener('keydown', function(event) {
        // Solo activar si no estamos en un input/textarea y la tecla es "B" o "b"
        if ((event.key === 'B' || event.key === 'b') && 
            event.target.tagName !== 'INPUT' && 
            event.target.tagName !== 'TEXTAREA' &&
            !event.ctrlKey && !event.altKey && !event.metaKey) {
            
            event.preventDefault();
            openModalBalance();
        }
    });
    
    // Actualizar saldos cada 30 segundos
    setInterval(actualizarSaldos, 30000);
    
    console.log('✅ Tesorería inicializada correctamente');
});

/**
 * Configura el formateo automático del input de monto
 */
function setupMontoInput(inputId) {
    const montoInput = document.getElementById(inputId);
    
    if (!montoInput) return;
    
    montoInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/[^0-9]/g, '');
        
        if (value) {
            // Formatear con separadores de miles
            value = parseInt(value).toLocaleString('es-CO');
            e.target.value = '$' + value;
        } else {
            e.target.value = '';
        }
    });
    
    montoInput.addEventListener('focus', function(e) {
        if (e.target.value === '$0' || e.target.value === '$') {
            e.target.value = '';
        }
    });
}

/**
 * Abre el modal para registrar un gasto
 */
function openModalGasto() {
    tipoEgresoActual = 'GASTO';
    document.getElementById('modal-title-text').textContent = 'Registrar Gasto';
    document.getElementById('tipo-egreso').value = 'GASTO';
    
    // Limpiar formulario
    document.getElementById('form-registrar-egreso').reset();
    
    // Cargar tipos de movimiento filtrados por GASTO
    cargarTiposMovimiento('GASTO');
    
    // Mostrar modal
    if (modalEgreso) {
        modalEgreso.show();
    }
}

/**
 * Abre el modal para registrar una compra
 */
function openModalCompra() {
    tipoEgresoActual = 'INVERSION';
    document.getElementById('modal-title-text').textContent = 'Registrar Compra';
    document.getElementById('tipo-egreso').value = 'INVERSION';
    
    // Limpiar formulario
    document.getElementById('form-registrar-egreso').reset();
    
    // Cargar tipos de movimiento filtrados por INVERSION
    cargarTiposMovimiento('INVERSION');
    
    // Mostrar modal
    if (modalEgreso) {
        modalEgreso.show();
    }
}

/**
 * Abre el modal para transferir fondos
 */
function openModalTransferencia() {
    // Limpiar formulario
    document.getElementById('form-transferir-fondos').reset();
    
    // Mostrar modal
    if (modalTransferencia) {
        modalTransferencia.show();
    }
}

/**
 * Carga los tipos de movimiento filtrados por tipo_base
 */
async function cargarTiposMovimiento(filtro) {
    try {
        const response = await fetch(window.TESORERIA_URLS.tipos_movimiento + `?filtro=${filtro}`);
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('tipo-movimiento');
            select.innerHTML = '<option value="">Seleccione categoría...</option>';
            
            data.tipos.forEach(tipo => {
                const option = document.createElement('option');
                option.value = tipo.id;
                option.textContent = tipo.nombre;
                select.appendChild(option);
            });
        } else {
            throw new Error('Error al cargar tipos de movimiento');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar las categorías',
            confirmButtonColor: '#2e7d32'
        });
    }
}

/**
 * Registra un egreso (gasto o compra)
 */
async function registrarEgreso() {
    // Obtener valores del formulario
    const form = document.getElementById('form-registrar-egreso');
    const formData = new FormData(form);
    
    // Validar campos requeridos
    const tipoMovimientoId = document.getElementById('tipo-movimiento').value;
    const origen = document.getElementById('origen-fondos').value;
    const montoStr = document.getElementById('monto-egreso').value;
    const descripcion = document.getElementById('descripcion-egreso').value;
    
    if (!tipoMovimientoId || !origen || !montoStr || !descripcion) {
        Swal.fire({
            icon: 'warning',
            title: 'Campos incompletos',
            text: 'Por favor complete todos los campos requeridos',
            confirmButtonColor: '#2e7d32'
        });
        return;
    }
    
    // Convertir monto a número (quitar $ y separadores)
    const monto = parseFloat(montoStr.replace(/[^0-9]/g, ''));
    
    if (isNaN(monto) || monto <= 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Monto inválido',
            text: 'Por favor ingrese un monto válido mayor a cero',
            confirmButtonColor: '#2e7d32'
        });
        return;
    }
    
    // Preparar datos para enviar
    const data = {
        tipo_movimiento_id: tipoMovimientoId,
        origen: origen,
        monto: monto,
        descripcion: descripcion,
        referencia: document.getElementById('referencia-egreso').value || ''
    };
    
    // Mostrar loading
    Swal.fire({
        title: 'Registrando...',
        text: 'Por favor espere',
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    try {
        const csrftoken = getCookie('csrftoken');
        
        const response = await fetch(window.TESORERIA_URLS.registrar_egreso, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal
            modalEgreso.hide();
            
            // Mostrar éxito
            Swal.fire({
                icon: 'success',
                title: '¡Registrado!',
                text: result.message,
                timer: 2000,
                showConfirmButton: false
            });
            
            // Recargar página después de 2 segundos
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error(result.error || 'Error al registrar egreso');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo registrar el egreso',
            confirmButtonColor: '#d32f2f'
        });
    }
}

/**
 * Realiza una transferencia entre cuentas
 */
async function realizarTransferencia() {
    // Obtener valores del formulario
    const cuentaOrigen = document.getElementById('cuenta-origen').value;
    const cuentaDestino = document.getElementById('cuenta-destino').value;
    const montoStr = document.getElementById('monto-transferencia').value;
    const descripcion = document.getElementById('descripcion-transferencia').value;
    
    console.log('DEBUG - Valores capturados:', {
        cuentaOrigen,
        cuentaDestino,
        montoStr,
        descripcion
    });
    
    // Validar campos
    if (!cuentaOrigen || cuentaOrigen === '') {
        Swal.fire({
            icon: 'warning',
            title: 'Origen no seleccionado',
            text: 'Por favor seleccione la cuenta de origen',
            confirmButtonColor: '#2e7d32'
        });
        return;
    }
    
    if (!cuentaDestino || cuentaDestino === '') {
        Swal.fire({
            icon: 'warning',
            title: 'Destino no seleccionado',
            text: 'Por favor seleccione la cuenta de destino',
            confirmButtonColor: '#2e7d32'
        });
        return;
    }
    
    if (!montoStr || !descripcion) {
        Swal.fire({
            icon: 'warning',
            title: 'Campos incompletos',
            text: 'Por favor complete el monto y la descripción',
            confirmButtonColor: '#2e7d32'
        });
        return;
    }
    
    if (cuentaOrigen === cuentaDestino) {
        Swal.fire({
            icon: 'warning',
            title: 'Error',
            text: 'El origen y destino no pueden ser iguales',
            confirmButtonColor: '#d32f2f'
        });
        return;
    }
    
    // Convertir monto a número
    const monto = parseFloat(montoStr.replace(/[^0-9]/g, ''));
    
    if (isNaN(monto) || monto <= 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Monto inválido',
            text: 'Por favor ingrese un monto válido mayor a cero',
            confirmButtonColor: '#2e7d32'
        });
        return;
    }
    
    // Preparar datos - Convertir a número si no es "CAJA"
    const origenValue = cuentaOrigen === 'CAJA' ? 'CAJA' : parseInt(cuentaOrigen);
    const destinoValue = cuentaDestino === 'CAJA' ? 'CAJA' : parseInt(cuentaDestino);
    
    const data = {
        origen: origenValue,
        destino_id: destinoValue,
        monto: monto,
        descripcion: descripcion
    };
    
    console.log('DEBUG - Datos a enviar:', data);
    
    // Mostrar loading
    Swal.fire({
        title: 'Transfiriendo...',
        text: 'Por favor espere',
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    try {
        const csrftoken = getCookie('csrftoken');
        
        const response = await fetch(window.TESORERIA_URLS.transferir_fondos, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal
            modalTransferencia.hide();
            
            // Mostrar éxito
            Swal.fire({
                icon: 'success',
                title: '¡Transferencia exitosa!',
                text: result.message,
                timer: 2000,
                showConfirmButton: false
            });
            
            // Recargar página
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error(result.error || 'Error al transferir fondos');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo realizar la transferencia',
            confirmButtonColor: '#d32f2f'
        });
    }
}

/**
 * Actualiza los saldos de todas las cuentas
 */
async function actualizarSaldos() {
    try {
        const response = await fetch(window.TESORERIA_URLS.saldos);
        const data = await response.json();
        
        if (data.success) {
            // Actualizar Caja
            const saldoCajaEl = document.getElementById('saldo-caja');
            if (saldoCajaEl && data.caja) {
                saldoCajaEl.textContent = `$${formatNumber(data.caja.saldo)}`;
            }
            
            // Actualizar Banco
            const saldoBancoEl = document.getElementById('saldo-banco');
            if (saldoBancoEl && data.banco) {
                saldoBancoEl.textContent = `$${formatNumber(data.banco.saldo)}`;
            }
            
            // Actualizar Reserva
            const saldoReservaEl = document.getElementById('saldo-reserva');
            if (saldoReservaEl && data.reserva) {
                saldoReservaEl.textContent = `$${formatNumber(data.reserva.saldo)}`;
            }
            
            // Actualizar Total
            const saldoTotalEl = document.getElementById('saldo-total');
            if (saldoTotalEl) {
                const total = (data.caja?.saldo || 0) + (data.banco?.saldo || 0) + (data.reserva?.saldo || 0);
                saldoTotalEl.textContent = `$${formatNumber(total)}`;
            }
            
            console.log('✅ Saldos actualizados');
        }
    } catch (error) {
        console.error('❌ Error al actualizar saldos:', error);
    }
}

/**
 * Formatea un número con separadores de miles
 */
function formatNumber(num) {
    return Math.round(num).toLocaleString('es-CO');
}

/**
 * Abre el modal de balance/ajuste de cuentas
 */
function openModalBalance() {
    console.log('🔧 Abriendo modal de balance...');
    
    // Limpiar formulario
    document.getElementById('form-balance-cuentas').reset();
    
    // Resetear diferencias
    resetearDiferencias();
    
    // Mostrar modal
    if (modalBalance) {
        modalBalance.show();
    }
}

/**
 * Configura los inputs de balance con formateo y cálculo de diferencias
 */
function setupBalanceInputs() {
    const balanceInputs = document.querySelectorAll('.balance-input');
    
    balanceInputs.forEach(input => {
        // Formateo de números
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9]/g, '');
            
            if (value) {
                value = parseInt(value).toLocaleString('es-CO');
                e.target.value = '$' + value;
            } else {
                e.target.value = '';
            }
            
            // Calcular diferencia
            calcularDiferencia(e.target);
        });
        
        input.addEventListener('focus', function(e) {
            if (e.target.value === '$0' || e.target.value === '$') {
                e.target.value = '';
            }
        });
        
        input.addEventListener('blur', function(e) {
            calcularDiferencia(e.target);
            actualizarResumenCambios();
        });
    });
}

/**
 * Calcula la diferencia entre saldo sistema y saldo real
 */
function calcularDiferencia(input) {
    const cuenta = input.dataset.cuenta;
    const saldoSistema = parseFloat(input.dataset.saldoSistema) || 0;
    const saldoRealStr = input.value.replace(/[^0-9]/g, '');
    const saldoReal = parseFloat(saldoRealStr) || 0;
    
    const diferencia = saldoReal - saldoSistema;
    const diferenciaEl = document.getElementById(`diferencia-${cuenta}`);
    
    if (input.value && saldoRealStr) {
        // Hay un valor ingresado
        if (diferencia === 0) {
            diferenciaEl.textContent = '$0';
            diferenciaEl.className = 'fw-bold diferencia-valor text-muted';
        } else if (diferencia > 0) {
            diferenciaEl.textContent = `+$${formatNumber(Math.abs(diferencia))}`;
            diferenciaEl.className = 'fw-bold diferencia-valor text-success';
        } else {
            diferenciaEl.textContent = `-$${formatNumber(Math.abs(diferencia))}`;
            diferenciaEl.className = 'fw-bold diferencia-valor text-danger';
        }
    } else {
        // No hay valor ingresado
        diferenciaEl.textContent = '$0';
        diferenciaEl.className = 'fw-bold diferencia-valor text-muted';
    }
}

/**
 * Resetea todas las diferencias
 */
function resetearDiferencias() {
    const diferencias = document.querySelectorAll('.diferencia-valor');
    diferencias.forEach(diff => {
        diff.textContent = '$0';
        diff.className = 'fw-bold diferencia-valor text-muted';
    });
    
    // Ocultar resumen de cambios
    document.getElementById('resumen-cambios').style.display = 'none';
    document.getElementById('btn-guardar-balance').disabled = true;
}

/**
 * Actualiza el resumen de cambios
 */
function actualizarResumenCambios() {
    const cambios = [];
    const balanceInputs = document.querySelectorAll('.balance-input');
    
    balanceInputs.forEach(input => {
        const cuenta = input.dataset.cuenta;
        const saldoSistema = parseFloat(input.dataset.saldoSistema) || 0;
        const saldoRealStr = input.value.replace(/[^0-9]/g, '');
        const saldoReal = parseFloat(saldoRealStr) || 0;
        
        if (input.value && saldoRealStr && saldoReal !== saldoSistema) {
            const diferencia = saldoReal - saldoSistema;
            const nombreCuenta = cuenta === 'caja' ? 'Dinero en Caja' : 
                                cuenta === 'banco' ? 'Banco Principal' : 'Dinero Guardado';
            
            cambios.push({
                cuenta: nombreCuenta,
                saldoSistema: saldoSistema,
                saldoReal: saldoReal,
                diferencia: diferencia
            });
        }
    });
    
    const resumenEl = document.getElementById('resumen-cambios');
    const listaCambiosEl = document.getElementById('lista-cambios');
    const btnGuardar = document.getElementById('btn-guardar-balance');
    
    if (cambios.length > 0) {
        let html = '<ul class="mb-0">';
        cambios.forEach(cambio => {
            const tipoClase = cambio.diferencia > 0 ? 'text-success' : 'text-danger';
            const signo = cambio.diferencia > 0 ? '+' : '';
            html += `<li><strong>${cambio.cuenta}:</strong> $${formatNumber(cambio.saldoSistema)} → $${formatNumber(cambio.saldoReal)} 
                     <span class="${tipoClase}">(${signo}$${formatNumber(Math.abs(cambio.diferencia))})</span></li>`;
        });
        html += '</ul>';
        
        listaCambiosEl.innerHTML = html;
        resumenEl.style.display = 'block';
        btnGuardar.disabled = false;
    } else {
        resumenEl.style.display = 'none';
        btnGuardar.disabled = true;
    }
}

/**
 * Aplica el balance/ajuste de cuentas
 */
async function aplicarBalance() {
    // Recopilar cambios
    const cambios = [];
    const balanceInputs = document.querySelectorAll('.balance-input');
    
    balanceInputs.forEach(input => {
        const cuenta = input.dataset.cuenta;
        const saldoSistema = parseFloat(input.dataset.saldoSistema) || 0;
        const saldoRealStr = input.value.replace(/[^0-9]/g, '');
        const saldoReal = parseFloat(saldoRealStr) || 0;
        
        if (input.value && saldoRealStr && saldoReal !== saldoSistema) {
            cambios.push({
                cuenta: cuenta,
                saldo_sistema: saldoSistema,
                saldo_real: saldoReal,
                diferencia: saldoReal - saldoSistema
            });
        }
    });
    
    if (cambios.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Sin cambios',
            text: 'No hay diferencias para ajustar',
            confirmButtonColor: '#FF6F00'
        });
        return;
    }
    
    // Confirmar cambios
    const confirmResult = await Swal.fire({
        icon: 'question',
        title: '¿Aplicar Balance?',
        html: `Se crearán <strong>${cambios.length} transacción(es)</strong> de balance.<br>
               <small class="text-muted">Esta acción no se puede deshacer.</small>`,
        showCancelButton: true,
        confirmButtonText: 'Sí, aplicar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#FF6F00',
        cancelButtonColor: '#6c757d'
    });
    
    if (!confirmResult.isConfirmed) {
        return;
    }
    
    // Mostrar loading
    Swal.fire({
        title: 'Aplicando balance...',
        text: 'Por favor espere',
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    try {
        const csrftoken = getCookie('csrftoken');
        
        const response = await fetch(window.TESORERIA_URLS.aplicar_balance, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ cambios: cambios })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal
            modalBalance.hide();
            
            // Mostrar éxito
            Swal.fire({
                icon: 'success',
                title: '¡Balance aplicado!',
                html: `${result.transacciones_creadas} transacción(es) creada(s).<br>
                       <small>${result.message}</small>`,
                timer: 3000,
                showConfirmButton: false
            });
            
            // Recargar página después de 3 segundos
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            throw new Error(result.error || 'Error al aplicar balance');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo aplicar el balance',
            confirmButtonColor: '#d32f2f'
        });
    }
}

/**
 * Obtiene el valor de una cookie
 */
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
