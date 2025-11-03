/**
 * JavaScript para el módulo de Facturación
 * Renzzo Eléctricos - Villavicencio, Meta
 */

(function() {
    'use strict';

    // Variables globales
    let clienteSeleccionado = null;
    let productosEnTabla = [];
    let productoIdCounter = 1;
    
    // URLs para AJAX
    const buscarProductosUrl = '/facturacion/ajax/buscar-productos/';

    // Inicialización cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        inicializarSelect2Cliente();
        inicializarBusquedaProductos();
        inicializarEventosTabla();
        inicializarBotonGenerarFactura();
    });

    /**
     * Inicializa el Select2 para buscar/seleccionar clientes
     */
    function inicializarSelect2Cliente() {
        const selectCliente = $('#cliente_id');
        
        // Primero cargar todos los clientes disponibles
        fetch('/facturacion/ajax/listar-clientes/?q=')
            .then(response => response.json())
            .then(data => {
                console.log('Clientes cargados:', data);
                
                // Limpiar opciones actuales (excepto placeholder y nuevo)
                selectCliente.find('option').not('[value=""], [value="nuevo"]').remove();
                
                // Agregar clientes al select
                if (data.results && data.results.length > 0) {
                    data.results.forEach(cliente => {
                        const option = new Option(
                            cliente.text,
                            cliente.id,
                            false,
                            false
                        );
                        // Guardar datos adicionales del cliente
                        $(option).data('cliente', cliente);
                        selectCliente.append(option);
                    });
                }
                
                // Ahora inicializar Select2
                selectCliente.select2({
                    theme: 'bootstrap-5',
                    placeholder: '-- Seleccionar Cliente --',
                    allowClear: true,
                    language: {
                        noResults: function() {
                            return 'No se encontraron clientes';
                        },
                        searching: function() {
                            return 'Buscando...';
                        }
                    },
                    // Función personalizada para buscar en nombre, NIT y correo
                    matcher: function(params, data) {
                        // Si no hay término de búsqueda, mostrar todo
                        if ($.trim(params.term) === '') {
                            return data;
                        }
                        
                        // No filtrar la opción "nuevo"
                        if (data.id === 'nuevo') {
                            return data;
                        }
                        
                        // Obtener datos completos del cliente
                        const clienteData = $(data.element).data('cliente');
                        if (!clienteData) {
                            return null;
                        }
                        
                        // Convertir término de búsqueda a minúsculas
                        const termino = params.term.toLowerCase();
                        
                        // Buscar en nombre, NIT y email
                        const nombre = (clienteData.nombre || '').toLowerCase();
                        const nit = (clienteData.nit || '').toLowerCase();
                        const email = (clienteData.email || '').toLowerCase();
                        const texto = (data.text || '').toLowerCase();
                        
                        // Si coincide con alguno de los campos, mostrar
                        if (nombre.indexOf(termino) > -1 || 
                            nit.indexOf(termino) > -1 || 
                            email.indexOf(termino) > -1 ||
                            texto.indexOf(termino) > -1) {
                            return data;
                        }
                        
                        // No hay coincidencia
                        return null;
                    },
                    templateResult: formatearOpcionCliente,
                    templateSelection: formatearSeleccionCliente
                });
                
                console.log('Select2 inicializado con', selectCliente.find('option').length - 1, 'clientes');
            })
            .catch(error => {
                console.error('Error al cargar clientes:', error);
                
                // Inicializar Select2 sin clientes
                selectCliente.select2({
                    theme: 'bootstrap-5',
                    placeholder: '-- Seleccionar Cliente --',
                    allowClear: true,
                    language: {
                        noResults: function() {
                            return 'Error al cargar clientes. Recargue la página.';
                        }
                    }
                });
            });

        // Evento cuando se selecciona un cliente
        selectCliente.on('select2:select', function(e) {
            const data = e.params.data;
            
            if (data.id === 'nuevo') {
                // Abrir modal para crear nuevo cliente
                abrirModalCrearCliente();
                // Resetear select
                selectCliente.val(null).trigger('change');
            } else {
                // Obtener los datos completos del cliente desde el option
                const selectedOption = selectCliente.find('option:selected');
                const clienteCompleto = selectedOption.data('cliente');
                
                console.log('Cliente seleccionado:', clienteCompleto);
                
                // Si los datos completos existen, usarlos; si no, usar los básicos
                const clienteData = clienteCompleto || data;
                
                // Mostrar información del cliente seleccionado
                mostrarInfoCliente(clienteData);
            }
        });

        // Evento cuando se limpia la selección
        selectCliente.on('select2:clear', function() {
            ocultarInfoCliente();
        });
    }

    /**
     * Formatea las opciones en el dropdown de Select2
     */
    function formatearOpcionCliente(cliente) {
        if (!cliente.id) {
            return cliente.text;
        }

        // Si es la opción "nuevo", mostrar sin formato especial (solo el texto)
        if (cliente.id === 'nuevo') {
            return $('<span class="cliente-opcion-nuevo"><i class="fas fa-plus-circle"></i> ' + cliente.text + '</span>');
        }

        // Obtener datos del elemento (pueden estar en data-cliente o directamente en el objeto)
        let datosCliente = cliente;
        if (cliente.element) {
            const elementData = $(cliente.element).data('cliente');
            if (elementData) {
                datosCliente = elementData;
            }
        }

        // Para clientes reales, mostrar el formato completo con NIT y Email
        const $opcion = $(
            '<div class="cliente-opcion">' +
                '<div class="cliente-nombre">' + (datosCliente.nombre || cliente.text) + '</div>' +
                '<div class="cliente-detalles">' +
                    '<small>NIT: ' + (datosCliente.nit || '-') + ' | Email: ' + (datosCliente.email || '-') + '</small>' +
                '</div>' +
            '</div>'
        );

        return $opcion;
    }

    /**
     * Formatea la selección en el input de Select2
     */
    function formatearSeleccionCliente(cliente) {
        if (cliente.isNew) {
            return '-- Seleccionar Cliente --';
        }
        return cliente.text;
    }

    /**
     * Muestra la información del cliente seleccionado
     */
    function mostrarInfoCliente(cliente) {
        clienteSeleccionado = cliente;
        
        // Llenar los campos de información
        document.getElementById('infoNombre').textContent = cliente.nombre || '-';
        document.getElementById('infoNit').textContent = cliente.nit || '-';
        document.getElementById('infoEmail').textContent = cliente.email || '-';
        document.getElementById('infoTelefono').textContent = cliente.telefono || '-';
        document.getElementById('infoDireccion').textContent = cliente.direccion || '-';
        
        // Mostrar el contenedor de información
        document.getElementById('clienteInfo').style.display = 'block';
    }

    /**
     * Oculta la información del cliente
     */
    function ocultarInfoCliente() {
        clienteSeleccionado = null;
        document.getElementById('clienteInfo').style.display = 'none';
    }

    /**
     * Abre el modal de SweetAlert2 para crear un nuevo cliente
     */
    function abrirModalCrearCliente() {
        Swal.fire({
            title: '<i class="fas fa-user-plus"></i> Crear Nuevo Cliente',
            html: generarHTMLFormularioCliente(),
            width: '800px',
            showCancelButton: true,
            confirmButtonText: '<i class="fas fa-save"></i> Guardar Cliente',
            cancelButtonText: '<i class="fas fa-times"></i> Cancelar',
            customClass: {
                confirmButton: 'btn btn-success',
                cancelButton: 'btn btn-secondary'
            },
            buttonsStyling: false,
            didOpen: () => {
                // Inicializar Select2 para departamentos y ciudades
                inicializarSelect2Modal();
                // Focus en el primer campo
                document.getElementById('modal_nombre_completo').focus();
            },
            preConfirm: () => {
                return validarYObtenerDatosCliente();
            }
        }).then((result) => {
            if (result.isConfirmed) {
                crearClienteAjax(result.value);
            }
        });
    }

    /**
     * Inicializa Select2 para departamentos y ciudades en el modal
     */
    function inicializarSelect2Modal() {
        // Cargar departamentos
        fetch('/static/facturacion/data/departamentos.json')
            .then(response => response.json())
            .then(data => {
                const selectDepartamento = $('#modal_departamento');
                selectDepartamento.select2({
                    theme: 'bootstrap-5',
                    placeholder: 'Seleccione un departamento',
                    allowClear: true,
                    dropdownParent: $('.swal2-popup'),
                    data: data.departamentos.map(dept => ({
                        id: dept.id,
                        text: dept.nombre
                    })),
                    language: {
                        noResults: function() {
                            return 'No se encontraron departamentos';
                        }
                    }
                });

                // Evento cuando se selecciona un departamento
                selectDepartamento.on('select2:select', function(e) {
                    cargarCiudadesPorDepartamento(e.params.data.id);
                });

                // Limpiar ciudades cuando se limpia el departamento
                selectDepartamento.on('select2:clear', function() {
                    $('#modal_ciudad').empty().trigger('change');
                });
            })
            .catch(error => {
                console.error('Error al cargar departamentos:', error);
            });

        // Inicializar Select2 para ciudades (vacío inicialmente)
        const selectCiudad = $('#modal_ciudad');
        selectCiudad.select2({
            theme: 'bootstrap-5',
            placeholder: 'Primero seleccione un departamento',
            allowClear: true,
            dropdownParent: $('.swal2-popup'),
            language: {
                noResults: function() {
                    return 'No se encontraron ciudades';
                }
            }
        });
    }

    /**
     * Carga las ciudades según el departamento seleccionado
     */
    function cargarCiudadesPorDepartamento(departamentoId) {
        fetch('/static/facturacion/data/ciudades.json')
            .then(response => response.json())
            .then(data => {
                // Filtrar ciudades por departamento
                const ciudadesDelDepartamento = data.ciudades
                    .filter(ciudad => ciudad.departamento_id === departamentoId)
                    .map(ciudad => ({
                        id: ciudad.nombre,
                        text: ciudad.nombre
                    }));

                // Actualizar Select2 de ciudades
                const selectCiudad = $('#modal_ciudad');
                selectCiudad.empty();
                selectCiudad.select2({
                    theme: 'bootstrap-5',
                    placeholder: 'Seleccione una ciudad',
                    allowClear: true,
                    dropdownParent: $('.swal2-popup'),
                    data: ciudadesDelDepartamento,
                    language: {
                        noResults: function() {
                            return 'No se encontraron ciudades';
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error al cargar ciudades:', error);
            });
    }

    /**
     * Genera el HTML del formulario para crear cliente
     */
    function generarHTMLFormularioCliente() {
        return `
            <div class="modal-section">
                <h4><i class="fas fa-id-card"></i> Datos del Cliente</h4>
                
                <div class="form-row">
                    <div class="form-field">
                        <label for="modal_nombre_completo">
                            Nombre Completo <span class="required-mark">*</span>
                        </label>
                        <input type="text" 
                               id="modal_nombre_completo" 
                               class="swal2-input" 
                               placeholder="Persona natural o empresa"
                               maxlength="200">
                    </div>
                    
                    <div class="form-field">
                        <label for="modal_nit">
                            NIT / Cédula <span class="required-mark">*</span>
                        </label>
                        <input type="text" 
                               id="modal_nit" 
                               class="swal2-input" 
                               placeholder="Número de identificación"
                               maxlength="20">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-field">
                        <label for="modal_email">
                            Correo Electrónico <span class="required-mark">*</span>
                        </label>
                        <input type="email" 
                               id="modal_email" 
                               class="swal2-input" 
                               placeholder="correo@ejemplo.com"
                               maxlength="100">
                    </div>

                    <div class="form-field">
                        <label for="modal_telefono">
                            Teléfono
                        </label>
                        <input type="text" 
                               id="modal_telefono" 
                               class="swal2-input" 
                               placeholder="Número de contacto"
                               maxlength="20">
                    </div>
                </div>

                <div class="form-row-full">
                    <div class="form-field">
                        <label for="modal_direccion">
                            Dirección
                        </label>
                        <input type="text" 
                               id="modal_direccion" 
                               class="swal2-input" 
                               placeholder="Dirección completa"
                               maxlength="300">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-field">
                        <label for="modal_departamento">
                            Departamento
                        </label>
                        <select id="modal_departamento" class="swal2-input">
                            <option value="">Seleccione un departamento</option>
                        </select>
                    </div>
                    
                    <div class="form-field">
                        <label for="modal_ciudad">
                            Ciudad
                        </label>
                        <select id="modal_ciudad" class="swal2-input">
                            <option value="">Primero seleccione un departamento</option>
                        </select>
                    </div>
                </div>

                <div class="info-text">
                    <i class="fas fa-info-circle"></i> Los campos marcados con <span class="required-mark">*</span> son obligatorios
                </div>
            </div>
        `;
    }
    /**
     * Valida y obtiene los datos del formulario de cliente
     */
    function validarYObtenerDatosCliente() {
        const nombreCompleto = document.getElementById('modal_nombre_completo').value.trim();
        const nit = document.getElementById('modal_nit').value.trim();
        const email = document.getElementById('modal_email').value.trim();
        const telefono = document.getElementById('modal_telefono').value.trim();
        const direccion = document.getElementById('modal_direccion').value.trim();
        const ciudad = document.getElementById('modal_ciudad').value.trim();
        const departamento = document.getElementById('modal_departamento').value.trim();

        // Validar campos requeridos
        if (!nombreCompleto) {
            Swal.showValidationMessage('El nombre completo es requerido');
            return false;
        }

        if (!nit) {
            Swal.showValidationMessage('El NIT/Cédula es requerido');
            return false;
        }

        if (!email) {
            Swal.showValidationMessage('El correo electrónico es requerido');
            return false;
        }

        // Validar formato de email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            Swal.showValidationMessage('El correo electrónico no es válido');
            return false;
        }

        return {
            nombre_completo: nombreCompleto,
            nit: nit,
            email: email,
            telefono: telefono,
            direccion: direccion,
            ciudad: ciudad,
            departamento: departamento
        };
    }

    /**
     * Crea el cliente mediante AJAX
     */
    function crearClienteAjax(datosCliente) {
        // Mostrar loading
        Swal.fire({
            title: 'Creando cliente...',
            text: 'Por favor espere',
            allowOutsideClick: false,
            allowEscapeKey: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // Obtener CSRF token
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Hacer la petición AJAX
        fetch('/facturacion/ajax/crear-cliente/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(datosCliente)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar loading y mostrar éxito
                Swal.fire({
                    icon: 'success',
                    title: '¡Cliente creado!',
                    text: data.message,
                    timer: 2000,
                    showConfirmButton: false
                });

                // Agregar el nuevo cliente al Select2 y seleccionarlo
                const selectCliente = $('#cliente_id');
                const newOption = new Option(
                    data.cliente.text,
                    data.cliente.id,
                    true,
                    true
                );
                $(newOption).data('cliente', data.cliente);
                selectCliente.append(newOption).trigger('change');

                // Mostrar información del cliente
                mostrarInfoCliente(data.cliente);
            } else {
                // Mostrar error
                Swal.fire({
                    icon: 'error',
                    title: 'Error al crear cliente',
                    text: data.message
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'No se pudo conectar con el servidor. Por favor, intente nuevamente.'
            });
        });
    }

    /**
     * Inicializa el sistema de búsqueda de productos
     */
    function inicializarBusquedaProductos() {
        const inputBuscar = $('#buscar_producto');
        
        // Inicializar Select2 con búsqueda AJAX
        inputBuscar.select2({
            theme: 'bootstrap-5',
            placeholder: 'Buscar producto por nombre o código...',
            allowClear: true,
            minimumInputLength: 1,
            language: {
                inputTooShort: function() {
                    return 'Escriba al menos 1 carácter para buscar';
                },
                searching: function() {
                    return 'Buscando productos...';
                },
                noResults: function() {
                    return 'No se encontraron productos';
                },
                errorLoading: function() {
                    return 'Error al cargar productos';
                }
            },
            ajax: {
                url: buscarProductosUrl,
                dataType: 'json',
                delay: 300,
                data: function(params) {
                    return {
                        q: params.term,
                        page: params.page || 1
                    };
                },
                processResults: function(data) {
                    console.log('Productos encontrados:', data.results);
                    return {
                        results: data.results.map(function(producto) {
                            return {
                                id: producto.id,
                                text: producto.text,
                                producto: producto
                            };
                        }),
                        pagination: data.pagination
                    };
                },
                cache: true
            },
            templateResult: function(data) {
                if (data.loading) {
                    return 'Buscando...';
                }
                
                if (!data.producto) {
                    return data.text;
                }
                
                const producto = data.producto;
                const precio = parseFloat(producto.precio || 0);
                
                return $(`
                    <div class="select2-producto-result">
                        <div class="fw-bold">${producto.text}</div>
                        <div class="small text-muted">
                            ${producto.upc ? `Código: ${producto.upc} | ` : ''}
                            Precio: $${precio.toFixed(2)}
                        </div>
                    </div>
                `);
            },
            templateSelection: function(data) {
                return data.text;
            }
        });
        
        // Evento cuando se selecciona un producto
        inputBuscar.on('select2:select', function(e) {
            const data = e.params.data;
            
            if (data.producto) {
                // Agregar producto de Oscar a la tabla
                const producto = {
                    id: `oscar_${data.producto.id}`,
                    descripcion: data.producto.text,
                    cantidad: 1,
                    precio_unitario: parseFloat(data.producto.precio || 0),
                    descuento: 0,
                    producto_oscar_id: data.producto.id
                };
                
                agregarProductoATabla(producto);
                
                // Limpiar select
                inputBuscar.val(null).trigger('change');
            }
        });
        
        // También mantener el evento ENTER para productos manuales
        inputBuscar.on('select2:close', function() {
            // Permitir que se pueda escribir texto libre y presionar ENTER
        });
    }

    /**
     * Agrega un producto manual (texto libre) a la tabla
     */
    function agregarProductoManual(descripcion) {
        const producto = {
            id: `manual_${productoIdCounter++}`,
            descripcion: descripcion,
            cantidad: 1,
            precio_unitario: 0,
            descuento: 0,
            producto_oscar_id: null
        };
        
        agregarProductoATabla(producto);
    }

    /**
     * Agrega un producto a la tabla
     */
    function agregarProductoATabla(producto) {
        // Agregar al array
        productosEnTabla.push(producto);
        
        // Ocultar mensaje de tabla vacía
        const emptyMessage = document.querySelector('.empty-table-message');
        if (emptyMessage) {
            emptyMessage.style.display = 'none';
        }
        
        // Crear fila
        const tbody = document.getElementById('productosTableBody');
        const tr = document.createElement('tr');
        tr.dataset.productoId = producto.id;
        
        const valorUnitario = parseFloat(producto.precio_unitario) - parseFloat(producto.descuento);
        const total = valorUnitario * parseFloat(producto.cantidad);
        
        tr.innerHTML = `
            <td>
                <input type="text" 
                       class="form-control form-control-sm campo-editable" 
                       data-campo="descripcion"
                       value="${producto.descripcion}">
            </td>
            <td>
                <input type="number" 
                       class="form-control form-control-sm campo-editable text-end" 
                       data-campo="cantidad"
                       value="${producto.cantidad}"
                       min="0.01"
                       step="0.01">
            </td>
            <td>
                <input type="number" 
                       class="form-control form-control-sm campo-editable text-end" 
                       data-campo="precio_unitario"
                       value="${producto.precio_unitario}"
                       min="0"
                       step="0.01">
            </td>
            <td>
                <input type="number" 
                       class="form-control form-control-sm campo-editable text-end" 
                       data-campo="descuento"
                       value="${producto.descuento}"
                       min="0"
                       step="0.01">
            </td>
            <td class="text-end valor-unitario">
                $${valorUnitario.toFixed(2)}
            </td>
            <td class="text-end total-producto">
                $${total.toFixed(2)}
            </td>
            <td class="text-center">
                <button type="button" 
                        class="btn btn-sm btn-danger btn-eliminar-producto"
                        title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(tr);
        
        // Recalcular totales
        calcularTotales();
    }

    /**
     * Inicializa eventos de la tabla (edición, eliminación)
     */
    function inicializarEventosTabla() {
        const tbody = document.getElementById('productosTableBody');
        
        // Delegación de eventos para campos editables
        tbody.addEventListener('input', function(e) {
            if (e.target.classList.contains('campo-editable')) {
                const tr = e.target.closest('tr');
                const productoId = tr.dataset.productoId;
                const campo = e.target.dataset.campo;
                const valor = e.target.value;
                
                // Actualizar en el array
                const producto = productosEnTabla.find(p => p.id === productoId);
                if (producto) {
                    producto[campo] = campo === 'descripcion' ? valor : parseFloat(valor) || 0;
                    actualizarFilaProducto(tr, producto);
                }
            }
        });
        
        // Delegación de eventos para botón eliminar
        tbody.addEventListener('click', function(e) {
            const btnEliminar = e.target.closest('.btn-eliminar-producto');
            if (btnEliminar) {
                const tr = btnEliminar.closest('tr');
                const productoId = tr.dataset.productoId;
                eliminarProducto(productoId, tr);
            }
        });
    }

    /**
     * Actualiza los valores calculados de una fila (valor unitario y total)
     */
    function actualizarFilaProducto(tr, producto) {
        const valorUnitario = parseFloat(producto.precio_unitario) - parseFloat(producto.descuento);
        const total = valorUnitario * parseFloat(producto.cantidad);
        
        tr.querySelector('.valor-unitario').textContent = `$${valorUnitario.toFixed(2)}`;
        tr.querySelector('.total-producto').textContent = `$${total.toFixed(2)}`;
        
        calcularTotales();
    }

    /**
     * Elimina un producto de la tabla
     */
    function eliminarProducto(productoId, tr) {
        Swal.fire({
            title: '¿Eliminar producto?',
            text: '¿Está seguro de eliminar este producto de la factura?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                // Eliminar del array
                productosEnTabla = productosEnTabla.filter(p => p.id !== productoId);
                
                // Eliminar fila
                tr.remove();
                
                // Mostrar mensaje si está vacía
                if (productosEnTabla.length === 0) {
                    const emptyMessage = document.querySelector('.empty-table-message');
                    if (emptyMessage) {
                        emptyMessage.style.display = '';
                    }
                }
                
                // Recalcular totales
                calcularTotales();
            }
        });
    }

    /**
     * Calcula todos los totales de la factura
     */
    function calcularTotales() {
        let subtotal = 0;
        let totalDescuentos = 0;
        
        productosEnTabla.forEach(producto => {
            const cantidad = parseFloat(producto.cantidad) || 0;
            const precioUnitario = parseFloat(producto.precio_unitario) || 0;
            const descuento = parseFloat(producto.descuento) || 0;
            
            subtotal += precioUnitario * cantidad;
            totalDescuentos += descuento * cantidad;
        });
        
        const subtotalNeto = subtotal - totalDescuentos;
        const iva = subtotalNeto * 0.19; // IVA 19%
        const totalPagar = subtotalNeto + iva;
        
        // Actualizar UI
        document.getElementById('totalSubtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('totalDescuentos').textContent = `$${totalDescuentos.toFixed(2)}`;
        document.getElementById('totalSubtotalNeto').textContent = `$${subtotalNeto.toFixed(2)}`;
        document.getElementById('totalIva').textContent = `$${iva.toFixed(2)}`;
        document.getElementById('totalPagar').textContent = `$${totalPagar.toFixed(2)}`;
        
        return {
            subtotal,
            totalDescuentos,
            subtotalNeto,
            iva,
            totalPagar
        };
    }

    /**
     * Inicializa el botón de generar factura
     */
    function inicializarBotonGenerarFactura() {
        const btnGenerar = document.getElementById('btnGenerarFactura');
        
        btnGenerar.addEventListener('click', function() {
            generarFactura();
        });
    }

    /**
     * Genera y guarda la factura completa
     */
    function generarFactura() {
        // Validar cliente
        if (!clienteSeleccionado || !clienteSeleccionado.id) {
            Swal.fire({
                icon: 'warning',
                title: 'Cliente requerido',
                text: 'Debe seleccionar un cliente para generar la factura'
            });
            return;
        }
        
        // Validar productos
        if (productosEnTabla.length === 0) {
            Swal.fire({
                icon: 'warning',
                title: 'Productos requeridos',
                text: 'Debe agregar al menos un producto a la factura'
            });
            return;
        }
        
        // Obtener datos del formulario
        const metodoPago = document.getElementById('metodo_pago').value;
        const condicionPago = document.getElementById('condicion_pago').value;
        const notas = document.getElementById('notas').value;
        
        // Preparar detalles para enviar
        const detalles = productosEnTabla.map(p => ({
            descripcion: p.descripcion,
            cantidad: parseFloat(p.cantidad),
            precio_unitario: parseFloat(p.precio_unitario),
            descuento: parseFloat(p.descuento),
            producto_id: p.producto_oscar_id
        }));
        
        // Datos a enviar
        const datosFactura = {
            cliente_id: clienteSeleccionado.id,
            detalles: detalles,
            metodo_pago: metodoPago,
            condicion_pago: condicionPago,
            notas: notas
        };
        
        // Mostrar loading
        Swal.fire({
            title: 'Generando factura...',
            text: 'Por favor espere',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        // Enviar al servidor
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/facturacion/ajax/guardar-factura/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(datosFactura)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mostrar éxito con información de la factura
                Swal.fire({
                    icon: 'success',
                    title: '¡Factura Generada!',
                    html: `
                        <div class="factura-exitosa">
                            <p><strong>Código:</strong> ${data.factura.codigo_factura}</p>
                            <p><strong>Total:</strong> $${parseFloat(data.factura.total_pagar).toFixed(2)}</p>
                            <p><strong>Fecha:</strong> ${data.factura.fecha_emision}</p>
                        </div>
                    `,
                    confirmButtonText: 'Aceptar'
                }).then(() => {
                    // Limpiar formulario para nueva factura
                    limpiarFormulario();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error al generar factura',
                    text: data.message
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'No se pudo conectar con el servidor. Por favor, intente nuevamente.'
            });
        });
    }

    /**
     * Limpia el formulario para crear una nueva factura
     */
    function limpiarFormulario() {
        // Limpiar cliente
        $('#cliente_id').val(null).trigger('change');
        clienteSeleccionado = null;
        document.getElementById('clienteInfo').style.display = 'none';
        
        // Limpiar productos
        productosEnTabla = [];
        const tbody = document.getElementById('productosTableBody');
        tbody.innerHTML = `
            <tr class="empty-table-message">
                <td colspan="7" class="text-center text-muted">
                    <i class="fas fa-box-open fa-2x mb-2"></i>
                    <p>No hay productos agregados. Use el buscador para agregar productos.</p>
                </td>
            </tr>
        `;
        
        // Limpiar totales
        calcularTotales();
        
        // Limpiar campos de pago
        document.getElementById('metodo_pago').value = 'EFECTIVO';
        document.getElementById('condicion_pago').value = 'CONTADO';
        document.getElementById('notas').value = '';
        
        // Limpiar búsqueda de productos (Select2)
        $('#buscar_producto').val(null).trigger('change');
    }

})();
