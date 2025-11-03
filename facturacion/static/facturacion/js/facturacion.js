/**
 * JavaScript para el módulo de Facturación
 * Renzzo Eléctricos - Villavicencio, Meta
 */

(function() {
    'use strict';

    // Variables globales
    let clienteSeleccionado = null;

    // Inicialización cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        inicializarSelect2Cliente();
    });

    /**
     * Inicializa el Select2 para buscar/seleccionar clientes
     */
    function inicializarSelect2Cliente() {
        const selectCliente = $('#cliente_id');
        
        selectCliente.select2({
            theme: 'bootstrap-5',
            placeholder: '-- Seleccionar Cliente --',
            allowClear: true,
            language: {
                inputTooShort: function() {
                    return 'Escriba al menos 2 caracteres para buscar';
                },
                searching: function() {
                    return 'Buscando clientes...';
                },
                noResults: function() {
                    return 'No se encontraron clientes';
                },
                errorLoading: function() {
                    return 'Error al cargar los resultados';
                }
            },
            ajax: {
                url: '/facturacion/ajax/listar-clientes/',
                dataType: 'json',
                delay: 300,
                data: function(params) {
                    return {
                        q: params.term || '',
                        page: params.page || 1
                    };
                },
                processResults: function(data) {
                    // Agregar opción "Crear Nuevo Cliente" al inicio
                    const results = [
                        {
                            id: 'nuevo',
                            text: '+ Crear Nuevo Cliente',
                            isNew: true
                        },
                        ...data.results
                    ];
                    
                    return {
                        results: results,
                        pagination: data.pagination
                    };
                },
                cache: true
            },
            minimumInputLength: 0,
            templateResult: formatearOpcionCliente,
            templateSelection: formatearSeleccionCliente
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
                // Mostrar información del cliente seleccionado
                mostrarInfoCliente(data);
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

        if (cliente.isNew) {
            return $('<span class="cliente-opcion-nuevo"><i class="fas fa-plus-circle"></i> ' + cliente.text + '</span>');
        }

        const $opcion = $(
            '<div class="cliente-opcion">' +
                '<div class="cliente-nombre">' + (cliente.nombre || cliente.text) + '</div>' +
                '<div class="cliente-detalles">' +
                    '<small>NIT: ' + (cliente.nit || '-') + ' | Email: ' + (cliente.email || '-') + '</small>' +
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

})();
