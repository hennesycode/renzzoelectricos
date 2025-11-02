/**
 * JavaScript para el Sistema de Caja Registradora
 * Renzzo Eléctricos - Villavicencio, Meta
 * 
 * Funcionalidades:
 * - Contador de dinero colombiano
 * - Cálculos automáticos
 * - Validaciones en tiempo real
 * - Confirmaciones con SweetAlert2
 */

/* ============================================
   CLASE PRINCIPAL - CajaManager
   ============================================ */
class CajaManager {
    constructor() {
        this.denominaciones = [];
        this.totalContado = 0;
        this.montoEsperado = 0;
        
        this.init();
    }

    /**
     * Inicializa el sistema de caja
     */
    init() {
        this.cargarDenominaciones();
        this.bindEvents();
        console.log('Sistema de Caja inicializado correctamente');
    }

    /**
     * Carga las denominaciones de moneda colombiana
     */
    cargarDenominaciones() {
        // Denominaciones estándar de Colombia (2025)
        this.denominaciones = [
            // Billetes
            { valor: 100000, tipo: 'BILLETE', activo: true },
            { valor: 50000, tipo: 'BILLETE', activo: true },
            { valor: 20000, tipo: 'BILLETE', activo: true },
            { valor: 10000, tipo: 'BILLETE', activo: true },
            { valor: 5000, tipo: 'BILLETE', activo: true },
            { valor: 2000, tipo: 'BILLETE', activo: true },
            { valor: 1000, tipo: 'BILLETE', activo: false }, // Menos común
            
            // Monedas
            { valor: 1000, tipo: 'MONEDA', activo: true },
            { valor: 500, tipo: 'MONEDA', activo: true },
            { valor: 200, tipo: 'MONEDA', activo: true },
            { valor: 100, tipo: 'MONEDA', activo: true },
            { valor: 50, tipo: 'MONEDA', activo: true }
        ];
    }

    /**
     * Vincula eventos globales
     */
    bindEvents() {
        // Formatear inputs de dinero
        document.querySelectorAll('input[type="number"][step="0.01"]').forEach(input => {
            input.addEventListener('input', this.formatearInputDinero.bind(this));
        });

        // Auto-calcular totales
        document.querySelectorAll('.cantidad-input').forEach(input => {
            input.addEventListener('input', this.actualizarTotal.bind(this));
        });
    }

    /**
     * Formatea inputs de dinero para mostrar formato colombiano
     */
    formatearInputDinero(event) {
        const input = event.target;
        let valor = input.value;
        
        // Permitir solo números y punto decimal
        valor = valor.replace(/[^0-9.]/g, '');
        
        // Asegurar solo un punto decimal
        const partes = valor.split('.');
        if (partes.length > 2) {
            valor = partes[0] + '.' + partes.slice(1).join('');
        }
        
        input.value = valor;
    }

    /**
     * Actualiza el total del contador de efectivo
     */
    actualizarTotal() {
        this.totalContado = 0;
        
        document.querySelectorAll('.denominacion-card').forEach(card => {
            const id = card.dataset.id;
            const valor = parseFloat(card.dataset.valor);
            const cantidadInput = document.getElementById(`cantidad_${id}`);
            const cantidad = parseInt(cantidadInput?.value) || 0;
            const subtotal = valor * cantidad;
            
            // Actualizar subtotal en la UI
            const subtotalElement = document.getElementById(`subtotal_${id}`);
            if (subtotalElement) {
                subtotalElement.textContent = this.formatearMoneda(subtotal);
            }
            
            this.totalContado += subtotal;
        });
        
        // Actualizar total en la UI
        const totalElement = document.getElementById('total-conteo');
        if (totalElement) {
            totalElement.textContent = this.formatearMoneda(this.totalContado);
        }
    }

    /**
     * Formatea un número como moneda colombiana
     */
    formatearMoneda(monto, incluirSimbolo = true) {
        const simbolo = incluirSimbolo ? '$' : '';
        return simbolo + monto.toLocaleString('es-CO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Calcula la diferencia entre monto esperado y declarado
     */
    calcularDiferencia(montoDeclardo, montoEsperado) {
        return montoDeclardo - montoEsperado;
    }

    /**
     * Muestra información de diferencias
     */
    mostrarDiferencia(diferencia) {
        const diferenciaInfo = document.getElementById('diferencia-info');
        const diferenciaMonto = document.getElementById('diferencia-monto');
        
        if (!diferenciaInfo || !diferenciaMonto) return;
        
        diferenciaInfo.style.display = 'block';
        
        if (diferencia === 0) {
            diferenciaInfo.className = 'alert alert-success mb-0';
            diferenciaMonto.innerHTML = '<i class="bi bi-check-circle"></i> Sin diferencias';
        } else if (diferencia > 0) {
            diferenciaInfo.className = 'alert alert-warning mb-0';
            diferenciaMonto.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Sobrante: ${this.formatearMoneda(diferencia)}`;
        } else {
            diferenciaInfo.className = 'alert alert-danger mb-0';
            diferenciaMonto.innerHTML = `<i class="bi bi-x-circle"></i> Faltante: ${this.formatearMoneda(Math.abs(diferencia))}`;
        }
    }

    /**
     * Limpia todos los contadores
     */
    limpiarConteo() {
        document.querySelectorAll('.cantidad-input').forEach(input => {
            input.value = 0;
        });
        this.actualizarTotal();
    }

    /**
     * Aplica el conteo al formulario principal
     */
    aplicarConteo() {
        const montoDeclarado = document.getElementById('monto_declarado');
        const montoDeclaradoHidden = document.getElementById('monto_declarado_hidden');
        
        if (montoDeclarado) {
            montoDeclarado.value = this.totalContado.toFixed(2);
        }
        
        if (montoDeclaradoHidden) {
            montoDeclaradoHidden.value = this.totalContado.toFixed(2);
        }
        
        // Actualizar diferencia si existe
        if (this.montoEsperado > 0) {
            const diferencia = this.calcularDiferencia(this.totalContado, this.montoEsperado);
            this.mostrarDiferencia(diferencia);
        }
        
        // Habilitar botón de cerrar caja
        const btnCerrar = document.getElementById('btn-cerrar-caja');
        if (btnCerrar) {
            btnCerrar.disabled = false;
        }
        
        return this.totalContado;
    }
}

/* ============================================
   UTILIDADES DE CAJA
   ============================================ */
const CajaUtils = {
    /**
     * Valida que un monto sea válido
     */
    validarMonto(monto) {
        const numero = parseFloat(monto);
        return !isNaN(numero) && numero >= 0;
    },

    /**
     * Convierte texto a número decimal
     */
    parseFloat(valor) {
        return parseFloat(valor.toString().replace(/[^0-9.-]/g, '')) || 0;
    },

    /**
     * Genera un ID único para elementos
     */
    generarId() {
        return 'caja_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * Calcula el tiempo transcurrido desde una fecha
     */
    calcularTiempoTranscurrido(fechaInicio) {
        const ahora = new Date();
        const inicio = new Date(fechaInicio);
        const diferencia = ahora - inicio;
        
        const horas = Math.floor(diferencia / (1000 * 60 * 60));
        const minutos = Math.floor((diferencia % (1000 * 60 * 60)) / (1000 * 60));
        
        return { horas, minutos, texto: `${horas}h ${minutos}m` };
    },

    /**
     * Formatea una fecha para mostrar en Colombia
     */
    formatearFecha(fecha, incluirHora = true) {
        const opciones = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            timeZone: 'America/Bogota'
        };
        
        if (incluirHora) {
            opciones.hour = '2-digit';
            opciones.minute = '2-digit';
        }
        
        return new Date(fecha).toLocaleDateString('es-CO', opciones);
    },

    /**
     * Muestra notificación de éxito
     */
    mostrarExito(titulo, mensaje, duracion = 3000) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'success',
                title: titulo,
                text: mensaje,
                timer: duracion,
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
        } else {
            console.log(`✅ ${titulo}: ${mensaje}`);
        }
    },

    /**
     * Muestra notificación de error
     */
    mostrarError(titulo, mensaje) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'error',
                title: titulo,
                text: mensaje,
                confirmButtonText: 'Entendido'
            });
        } else {
            console.error(`❌ ${titulo}: ${mensaje}`);
        }
    },

    /**
     * Confirma una acción con el usuario
     */
    async confirmarAccion(titulo, mensaje, tipo = 'warning') {
        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title: titulo,
                text: mensaje,
                icon: tipo,
                showCancelButton: true,
                confirmButtonColor: '#198754',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Cancelar'
            });
            return result.isConfirmed;
        } else {
            return confirm(`${titulo}\n\n${mensaje}`);
        }
    }
};

/* ============================================
   FUNCIONES GLOBALES PARA TEMPLATES
   ============================================ */

/**
 * Cambia la cantidad de una denominación
 */
function cambiarCantidad(denominacionId, incremento) {
    const input = document.getElementById(`cantidad_${denominacionId}`);
    if (!input) return;
    
    let cantidad = parseInt(input.value) || 0;
    cantidad = Math.max(0, cantidad + incremento);
    input.value = cantidad;
    
    // Actualizar total si el manager está disponible
    if (window.cajaManager) {
        window.cajaManager.actualizarTotal();
    } else {
        // Fallback manual
        actualizarTotal();
    }
}

/**
 * Actualiza el total del conteo (función global de respaldo)
 */
function actualizarTotal() {
    let total = 0;
    
    document.querySelectorAll('.denominacion-card').forEach(card => {
        const id = card.dataset.id;
        const valor = parseFloat(card.dataset.valor);
        const cantidad = parseInt(document.getElementById(`cantidad_${id}`)?.value) || 0;
        const subtotal = valor * cantidad;
        
        const subtotalElement = document.getElementById(`subtotal_${id}`);
        if (subtotalElement) {
            subtotalElement.textContent = `$${subtotal.toLocaleString('es-CO')}`;
        }
        
        total += subtotal;
    });
    
    const totalElement = document.getElementById('total-conteo');
    if (totalElement) {
        totalElement.textContent = `$${total.toLocaleString('es-CO', {minimumFractionDigits: 2})}`;
    }
}

/**
 * Limpia el conteo de efectivo
 */
function limpiarConteo() {
    if (window.cajaManager) {
        window.cajaManager.limpiarConteo();
    } else {
        document.querySelectorAll('.cantidad-input').forEach(input => {
            input.value = 0;
        });
        actualizarTotal();
    }
}

/**
 * Aplica el conteo al formulario
 */
function aplicarConteo() {
    if (window.cajaManager) {
        const total = window.cajaManager.aplicarConteo();
        
        // Cerrar modal si existe
        const modal = document.getElementById('modalConteo');
        if (modal && typeof bootstrap !== 'undefined') {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
        
        // Mostrar confirmación
        CajaUtils.mostrarExito(
            'Conteo aplicado',
            `Total: $${total.toLocaleString('es-CO', {minimumFractionDigits: 2})}`
        );
    }
}

/* ============================================
   INICIALIZACIÓN
   ============================================ */
document.addEventListener('DOMContentLoaded', function() {
    // Crear instancia global del manager
    window.cajaManager = new CajaManager();
    
    // Configurar formateo automático de fechas
    document.querySelectorAll('[data-fecha]').forEach(elemento => {
        const fecha = elemento.dataset.fecha;
        if (fecha) {
            elemento.textContent = CajaUtils.formatearFecha(fecha);
        }
    });
    
    // Auto-actualizar tiempos transcurridos
    const elementosTiempo = document.querySelectorAll('[data-fecha-inicio]');
    if (elementosTiempo.length > 0) {
        function actualizarTiempos() {
            elementosTiempo.forEach(elemento => {
                const fechaInicio = elemento.dataset.fechaInicio;
                if (fechaInicio) {
                    const tiempo = CajaUtils.calcularTiempoTranscurrido(fechaInicio);
                    elemento.textContent = tiempo.texto;
                }
            });
        }
        
        actualizarTiempos();
        setInterval(actualizarTiempos, 60000); // Cada minuto
    }
    
    console.log('✅ Sistema de Caja cargado completamente');
});

/* ============================================
   EXPORT PARA MÓDULOS (SI SE NECESITA)
   ============================================ */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CajaManager,
        CajaUtils
    };
}