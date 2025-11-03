/**
 * INFORMES DE CAJA - Sistema AJAX Completo
 * Renzzo Eléctricos - Villavicencio, Meta
 * 
 * Maneja filtros dinámicos, balance general, historial de arqueos
 * y flujo de efectivo sin recargar la página.
 */

(function() {
    'use strict';

    // ============================================================
    // VARIABLES GLOBALES
    // ============================================================
    let filtroActual = 'ultima_semana';
    let paginaActual = 1;
    const registrosPorPagina = 5;

    // ============================================================
    // UTILIDADES
    // ============================================================
    function formatearMoneda(valor) {
        const numero = parseFloat(valor) || 0;
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(numero);
    }

    function obtenerCSRFToken() {
        const name = 'csrftoken';
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

    function obtenerTextoFiltro(filtro) {
        const textos = {
            'dia_actual': 'Hoy',
            'dia_anterior': 'Ayer',
            'ultima_semana': 'Última Semana',
            'ultimos_30_dias': 'Últimos 30 Días',
            'ultimos_2_meses': 'Últimos 2 Meses',
            'ultimos_3_meses': 'Últimos 3 Meses',
            'rango_personalizado': 'Rango Personalizado'
        };
        return textos[filtro] || 'Última Semana';
    }

    // ============================================================
    // BALANCE GENERAL
    // ============================================================
    async function cargarBalanceGeneral(filtro = 'ultima_semana', fechaDesde = '', fechaHasta = '') {
        try {
            let url = `/caja/informes/balance-general/?filtro=${filtro}`;
            
            if (filtro === 'rango_personalizado' && fechaDesde && fechaHasta) {
                url += `&fecha_desde=${fechaDesde}&fecha_hasta=${fechaHasta}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': obtenerCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error('Error al cargar balance');
            }

            const data = await response.json();
            
            if (data.success) {
                actualizarBalanceUI(data.balance);
                
                // Actualizar texto del periodo
                const periodoTexto = obtenerTextoFiltro(filtro);
                document.getElementById('periodoBalance').querySelector('span').textContent = periodoTexto;
            }
        } catch (error) {
            console.error('Error al cargar balance:', error);
            mostrarError('Error al cargar el balance general');
        }
    }

    function actualizarBalanceUI(balance) {
        // Actualizar valores
        document.getElementById('totalGuardado').textContent = formatearMoneda(balance.total_dinero_guardado);
        document.getElementById('totalIngresos').textContent = formatearMoneda(balance.total_ingresos);
        document.getElementById('totalEgresos').textContent = formatearMoneda(balance.total_egresos);
        document.getElementById('flujoNeto').textContent = formatearMoneda(balance.flujo_neto);
        document.getElementById('numCajas').textContent = balance.num_cajas;
        document.getElementById('promedioDif').textContent = formatearMoneda(balance.promedio_diferencia);

        // Animar cards
        animarCards();
    }

    function animarCards() {
        const cards = document.querySelectorAll('.balance-card');
        cards.forEach((card, index) => {
            card.style.animation = 'none';
            setTimeout(() => {
                card.style.animation = `fadeIn 0.5s ease-in ${index * 0.1}s both`;
            }, 10);
        });
    }

    // ============================================================
    // HISTORIAL DE ARQUEOS
    // ============================================================
    async function cargarHistorialArqueos(pagina = 1, fechaDesde = '', fechaHasta = '') {
        try {
            mostrarLoading('loadingArqueos', true);
            
            let url = `/caja/informes/historial-arqueos/?pagina=${pagina}&por_pagina=${registrosPorPagina}`;
            
            if (fechaDesde) url += `&fecha_desde=${fechaDesde}`;
            if (fechaHasta) url += `&fecha_hasta=${fechaHasta}`;

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': obtenerCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error('Error al cargar historial');
            }

            const data = await response.json();
            
            if (data.success) {
                actualizarTablaArqueos(data.cajas);
                actualizarPaginacion(data.paginacion);
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
            mostrarError('Error al cargar el historial de arqueos');
        } finally {
            mostrarLoading('loadingArqueos', false);
        }
    }

    function actualizarTablaArqueos(cajas) {
        const tbody = document.getElementById('tablaArqueosBody');
        
        if (cajas.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="11" class="text-center">
                        <i class="bi bi-inbox"></i>
                        <p>No hay cajas registradas en este periodo</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = cajas.map(caja => {
            const claseDiferencia = caja.diferencia > 0 ? 'diferencia-positiva' : 
                                   caja.diferencia < 0 ? 'diferencia-negativa' : 
                                   'diferencia-cero';
            
            return `
                <tr>
                    <td>${caja.id}</td>
                    <td>${caja.cajero}</td>
                    <td>${caja.fecha_apertura}</td>
                    <td>${caja.fecha_cierre}</td>
                    <td>${formatearMoneda(caja.saldo_inicial)}</td>
                    <td style="color: var(--verde-claro);">${formatearMoneda(caja.total_entradas)}</td>
                    <td style="color: #e63946;">${formatearMoneda(caja.total_salidas)}</td>
                    <td style="font-weight: 600;">${formatearMoneda(caja.saldo_teorico)}</td>
                    <td style="font-weight: 600;">${formatearMoneda(caja.saldo_real)}</td>
                    <td class="${claseDiferencia}">${formatearMoneda(caja.diferencia)}</td>
                    <td>
                        <button class="btn-ver-detalle" onclick="abrirModalDetalle(${caja.id})">
                            <i class="bi bi-eye"></i>
                            Ver
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function actualizarPaginacion(paginacion) {
        const contenedor = document.getElementById('paginacionArqueos');
        const btnAnterior = document.getElementById('btnPagAnterior');
        const btnSiguiente = document.getElementById('btnPagSiguiente');
        const pagActualSpan = document.getElementById('pagActual');
        const pagTotalSpan = document.getElementById('pagTotal');
        const totalRegistrosSpan = document.getElementById('totalRegistros');

        if (paginacion.total_paginas > 1) {
            contenedor.style.display = 'flex';
        } else {
            contenedor.style.display = 'none';
        }

        pagActualSpan.textContent = paginacion.pagina_actual;
        pagTotalSpan.textContent = paginacion.total_paginas;
        totalRegistrosSpan.textContent = paginacion.total_registros;

        btnAnterior.disabled = !paginacion.tiene_anterior;
        btnSiguiente.disabled = !paginacion.tiene_siguiente;

        // Actualizar variable global
        paginaActual = paginacion.pagina_actual;
    }

    // ============================================================
    // FLUJO DE EFECTIVO
    // ============================================================
    async function cargarFlujoEfectivo(filtro = 'ultima_semana', fechaDesde = '', fechaHasta = '') {
        try {
            let url = `/caja/informes/flujo-efectivo/?filtro=${filtro}`;
            
            if (filtro === 'rango_personalizado' && fechaDesde && fechaHasta) {
                url += `&fecha_desde=${fechaDesde}&fecha_hasta=${fechaHasta}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': obtenerCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error('Error al cargar flujo');
            }

            const data = await response.json();
            
            if (data.success) {
                actualizarFlujoUI(data.flujo);
                
                // Actualizar texto del periodo
                const periodoTexto = obtenerTextoFiltro(filtro);
                document.getElementById('periodoFlujo').querySelector('span').textContent = periodoTexto;
            }
        } catch (error) {
            console.error('Error al cargar flujo:', error);
            mostrarError('Error al cargar el flujo de efectivo');
        }
    }

    function actualizarFlujoUI(flujo) {
        // Actualizar totales
        document.getElementById('flujoTotalIngresos').textContent = formatearMoneda(flujo.total_ingresos);
        document.getElementById('flujoTotalEgresos').textContent = formatearMoneda(flujo.total_egresos);
        document.getElementById('flujoResultado').textContent = formatearMoneda(flujo.flujo_neto);

        // Actualizar desglose de ingresos
        const ingresosContainer = document.getElementById('flujoIngresosDesglose');
        if (flujo.ingresos_por_tipo.length > 0) {
            ingresosContainer.innerHTML = flujo.ingresos_por_tipo.map(item => `
                <div class="desglose-item">
                    <div class="desglose-nombre">${item.tipo}</div>
                    <div class="desglose-valores">
                        <div class="desglose-monto">${formatearMoneda(item.total)}</div>
                        <div class="desglose-cantidad">${item.cantidad} movimiento${item.cantidad !== 1 ? 's' : ''}</div>
                    </div>
                </div>
            `).join('');
        } else {
            ingresosContainer.innerHTML = '<p class="no-data">Sin movimientos de ingreso</p>';
        }

        // Actualizar desglose de egresos
        const egresosContainer = document.getElementById('flujoEgresosDesglose');
        if (flujo.egresos_por_tipo.length > 0) {
            egresosContainer.innerHTML = flujo.egresos_por_tipo.map(item => `
                <div class="desglose-item" style="border-left-color: #e63946;">
                    <div class="desglose-nombre">${item.tipo}</div>
                    <div class="desglose-valores">
                        <div class="desglose-monto">${formatearMoneda(item.total)}</div>
                        <div class="desglose-cantidad">${item.cantidad} movimiento${item.cantidad !== 1 ? 's' : ''}</div>
                    </div>
                </div>
            `).join('');
        } else {
            egresosContainer.innerHTML = '<p class="no-data">Sin movimientos de egreso</p>';
        }

        // Actualizar clase del resultado según sea positivo o negativo
        const resultadoCard = document.getElementById('resultadoCard');
        const flujoNetoNum = parseFloat(flujo.flujo_neto) || 0;
        
        resultadoCard.classList.remove('positivo', 'negativo');
        if (flujoNetoNum >= 0) {
            resultadoCard.classList.add('positivo');
            document.getElementById('flujoResultadoLabel').textContent = 'Ganancia del Periodo';
        } else {
            resultadoCard.classList.add('negativo');
            document.getElementById('flujoResultadoLabel').textContent = 'Pérdida del Periodo';
        }
    }

    // ============================================================
    // UTILIDADES DE UI
    // ============================================================
    function mostrarLoading(elementId, mostrar) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = mostrar ? 'block' : 'none';
        }
    }

    function mostrarError(mensaje) {
        // Aquí podrías implementar SweetAlert2 o un sistema de notificaciones
        console.error(mensaje);
        alert(mensaje);
    }

    // ============================================================
    // EVENTOS
    // ============================================================
    function inicializarEventos() {
        // Botones de filtro rápido
        document.querySelectorAll('.btn-filtro').forEach(btn => {
            btn.addEventListener('click', function() {
                // Remover clase active de todos
                document.querySelectorAll('.btn-filtro').forEach(b => b.classList.remove('active'));
                
                // Agregar clase active al clickeado
                this.classList.add('active');
                
                // Obtener filtro
                const filtro = this.dataset.filtro;
                filtroActual = filtro;
                
                // Cargar datos
                cargarDatos(filtro);
            });
        });

        // Botón aplicar rango personalizado
        document.getElementById('btnAplicarRango').addEventListener('click', function() {
            const fechaDesde = document.getElementById('fechaDesde').value;
            const fechaHasta = document.getElementById('fechaHasta').value;
            
            if (!fechaDesde || !fechaHasta) {
                mostrarError('Debes seleccionar ambas fechas');
                return;
            }
            
            if (fechaDesde > fechaHasta) {
                mostrarError('La fecha de inicio no puede ser mayor que la fecha final');
                return;
            }
            
            // Remover active de botones de filtro
            document.querySelectorAll('.btn-filtro').forEach(b => b.classList.remove('active'));
            
            filtroActual = 'rango_personalizado';
            
            // Cargar datos con rango personalizado
            cargarDatos('rango_personalizado', fechaDesde, fechaHasta);
        });

        // Botones de paginación
        document.getElementById('btnPagAnterior').addEventListener('click', function() {
            if (paginaActual > 1) {
                cargarHistorialArqueos(paginaActual - 1);
            }
        });

        document.getElementById('btnPagSiguiente').addEventListener('click', function() {
            cargarHistorialArqueos(paginaActual + 1);
        });
    }

    // ============================================================
    // FUNCIÓN PRINCIPAL DE CARGA
    // ============================================================
    function cargarDatos(filtro = 'ultima_semana', fechaDesde = '', fechaHasta = '') {
        // Cargar balance general
        cargarBalanceGeneral(filtro, fechaDesde, fechaHasta);
        
        // Cargar historial de arqueos (primera página)
        paginaActual = 1;
        cargarHistorialArqueos(1, fechaDesde, fechaHasta);
        
        // Cargar flujo de efectivo
        cargarFlujoEfectivo(filtro, fechaDesde, fechaHasta);
    }

    // ============================================================
    // INICIALIZACIÓN
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {
        console.log('📊 Informes de Caja - Inicializando...');
        
        // Inicializar eventos
        inicializarEventos();
        
        // Cargar datos iniciales (última semana por defecto)
        cargarDatos('ultima_semana');
        
        console.log('✅ Informes de Caja - Listo');
    });

    // ============================================================
    // MODAL DETALLE DE CAJA
    // ============================================================
    window.abrirModalDetalle = async function(cajaId) {
        const modal = document.getElementById('modalDetalleCaja');
        const modalBody = document.getElementById('modalDetalleBody');
        const modalCajaId = document.getElementById('modalCajaId');
        
        // Mostrar modal
        modal.style.display = 'flex';
        modalCajaId.textContent = `#${cajaId}`;
        
        // Mostrar loading
        modalBody.innerHTML = `
            <div class="loading-modal">
                <i class="bi bi-arrow-repeat spin"></i>
                <p>Cargando información...</p>
            </div>
        `;
        
        try {
            const response = await fetch(`/caja/informes/detalle-caja/${cajaId}/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': obtenerCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Error al cargar detalle');
            }
            
            const data = await response.json();
            
            if (data.success) {
                renderizarDetalleModal(data.caja);
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        } catch (error) {
            console.error('Error:', error);
            modalBody.innerHTML = `
                <div class="loading-modal">
                    <i class="bi bi-exclamation-triangle" style="color: #e63946;"></i>
                    <p style="color: #e63946;">Error al cargar el detalle de la caja</p>
                </div>
            `;
        }
    };

    window.cerrarModalDetalle = function() {
        const modal = document.getElementById('modalDetalleCaja');
        modal.style.display = 'none';
    };

    // Cerrar modal al hacer clic en el overlay
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-detalle-overlay')) {
            cerrarModalDetalle();
        }
    });

    // Cerrar modal con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('modalDetalleCaja');
            if (modal.style.display === 'flex') {
                cerrarModalDetalle();
            }
        }
    });

    function renderizarDetalleModal(caja) {
        const modalBody = document.getElementById('modalDetalleBody');
        
        let html = `
            <!-- Información General -->
            <div class="modal-section">
                <div class="modal-section-title">
                    <i class="bi bi-info-circle"></i>
                    <span>Información General</span>
                </div>
                <div class="modal-info-grid">
                    <div class="modal-info-item">
                        <div class="modal-info-label">Cajero</div>
                        <div class="modal-info-value">${caja.cajero}</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">Estado</div>
                        <div class="modal-info-value">${caja.estado === 'CERRADA' ? '🔒 Cerrada' : '🟢 Abierta'}</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">Fecha de Apertura</div>
                        <div class="modal-info-value">${caja.fecha_apertura}</div>
                    </div>
                    ${caja.fecha_cierre ? `
                    <div class="modal-info-item">
                        <div class="modal-info-label">Fecha de Cierre</div>
                        <div class="modal-info-value">${caja.fecha_cierre}</div>
                    </div>
                    ` : ''}
                </div>
            </div>

            <!-- Apertura -->
            <div class="modal-section">
                <div class="modal-section-title">
                    <i class="bi bi-unlock"></i>
                    <span>Apertura de Caja</span>
                </div>
                <div class="modal-info-grid">
                    <div class="modal-info-item">
                        <div class="modal-info-label">Monto Inicial</div>
                        <div class="modal-info-value positivo">${formatearMoneda(caja.monto_inicial)}</div>
                    </div>
                    ${caja.observaciones_apertura !== '-' ? `
                    <div class="modal-info-item" style="grid-column: span 2;">
                        <div class="modal-info-label">Observaciones</div>
                        <div class="modal-info-value" style="font-size: 14px;">${caja.observaciones_apertura}</div>
                    </div>
                    ` : ''}
                </div>
                
                ${caja.conteo_apertura ? `
                <h4 style="color: var(--text-light); margin: 20px 0 10px 0; font-size: 16px;">
                    <i class="bi bi-cash-stack"></i> Denominaciones de Apertura
                </h4>
                <table class="modal-denominaciones-table">
                    <thead>
                        <tr>
                            <th>Denominación</th>
                            <th>Tipo</th>
                            <th>Cantidad</th>
                            <th>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${caja.conteo_apertura.detalles.map(d => `
                            <tr>
                                <td>
                                    <i class="denom-icon bi ${d.tipo === 'BILLETE' ? 'bi-cash' : 'bi-coin'}"></i>
                                    ${formatearMoneda(d.valor)}
                                </td>
                                <td>${d.tipo === 'BILLETE' ? '💵 Billete' : '🪙 Moneda'}</td>
                                <td style="font-weight: 600;">${d.cantidad}</td>
                                <td style="font-weight: 600; color: var(--verde-claro);">${formatearMoneda(d.subtotal)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                ` : '<p class="no-denominaciones">No se registraron denominaciones en la apertura</p>'}
            </div>

            <!-- Movimientos -->
            <div class="modal-section">
                <div class="modal-section-title">
                    <i class="bi bi-arrow-left-right"></i>
                    <span>Movimientos de Caja (${caja.num_movimientos})</span>
                </div>
                
                ${caja.movimientos.length > 0 ? `
                <div style="overflow-x: auto;">
                    <table class="modal-movimientos-table">
                        <thead>
                            <tr>
                                <th>Fecha/Hora</th>
                                <th>Tipo</th>
                                <th>Categoría</th>
                                <th>Monto</th>
                                <th>Descripción</th>
                                <th>Referencia</th>
                                <th>Usuario</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${caja.movimientos.map(m => `
                                <tr>
                                    <td style="white-space: nowrap;">${m.fecha}</td>
                                    <td>
                                        <span class="${m.tipo === 'INGRESO' ? 'badge-ingreso' : 'badge-egreso'}">
                                            ${m.tipo === 'INGRESO' ? '⬇️ Ingreso' : '⬆️ Egreso'}
                                        </span>
                                    </td>
                                    <td>${m.tipo_movimiento}</td>
                                    <td style="font-weight: 600; color: ${m.tipo === 'INGRESO' ? 'var(--verde-claro)' : '#e63946'};">
                                        ${formatearMoneda(m.monto)}
                                    </td>
                                    <td>${m.descripcion}</td>
                                    <td>${m.referencia}</td>
                                    <td>${m.usuario}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <!-- Totales de Movimientos -->
                <div class="modal-totales">
                    <div class="modal-total-card">
                        <div class="modal-total-label">Total Ingresos</div>
                        <div class="modal-total-value" style="color: var(--verde-claro);">
                            ${formatearMoneda(caja.total_ingresos)}
                        </div>
                    </div>
                    <div class="modal-total-card">
                        <div class="modal-total-label">Total Egresos</div>
                        <div class="modal-total-value" style="color: #e63946;">
                            ${formatearMoneda(caja.total_egresos)}
                        </div>
                    </div>
                    <div class="modal-total-card">
                        <div class="modal-total-label">Saldo Teórico</div>
                        <div class="modal-total-value">
                            ${formatearMoneda(caja.saldo_teorico)}
                        </div>
                    </div>
                </div>
                ` : '<p class="no-movimientos">No se registraron movimientos en esta caja</p>'}
            </div>

            <!-- Cierre -->
            ${caja.estado === 'CERRADA' ? `
            <div class="modal-section">
                <div class="modal-section-title">
                    <i class="bi bi-lock"></i>
                    <span>Cierre de Caja</span>
                </div>
                <div class="modal-info-grid">
                    <div class="modal-info-item">
                        <div class="modal-info-label">Saldo Real Contado</div>
                        <div class="modal-info-value">${formatearMoneda(caja.monto_final_declarado)}</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">Diferencia</div>
                        <div class="modal-info-value ${caja.diferencia > 0 ? 'positivo' : caja.diferencia < 0 ? 'negativo' : ''}">
                            ${formatearMoneda(caja.diferencia)}
                            ${caja.diferencia > 0 ? ' (Sobrante)' : caja.diferencia < 0 ? ' (Faltante)' : ' (Cuadre Perfecto)'}
                        </div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">Dinero en Caja</div>
                        <div class="modal-info-value">${formatearMoneda(caja.dinero_en_caja)}</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">Dinero Guardado</div>
                        <div class="modal-info-value">${formatearMoneda(caja.dinero_guardado)}</div>
                    </div>
                    ${caja.observaciones_cierre !== '-' ? `
                    <div class="modal-info-item" style="grid-column: span 2;">
                        <div class="modal-info-label">Observaciones de Cierre</div>
                        <div class="modal-info-value" style="font-size: 14px;">${caja.observaciones_cierre}</div>
                    </div>
                    ` : ''}
                </div>
                
                ${caja.conteo_cierre ? `
                <h4 style="color: var(--text-light); margin: 20px 0 10px 0; font-size: 16px;">
                    <i class="bi bi-cash-stack"></i> Denominaciones de Cierre
                </h4>
                <table class="modal-denominaciones-table">
                    <thead>
                        <tr>
                            <th>Denominación</th>
                            <th>Tipo</th>
                            <th>Cantidad</th>
                            <th>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${caja.conteo_cierre.detalles.map(d => `
                            <tr>
                                <td>
                                    <i class="denom-icon bi ${d.tipo === 'BILLETE' ? 'bi-cash' : 'bi-coin'}"></i>
                                    ${formatearMoneda(d.valor)}
                                </td>
                                <td>${d.tipo === 'BILLETE' ? '💵 Billete' : '🪙 Moneda'}</td>
                                <td style="font-weight: 600;">${d.cantidad}</td>
                                <td style="font-weight: 600; color: var(--verde-claro);">${formatearMoneda(d.subtotal)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                ` : '<p class="no-denominaciones">No se registraron denominaciones en el cierre</p>'}
            </div>
            ` : ''}
        `;
        
        modalBody.innerHTML = html;
    }

})();
