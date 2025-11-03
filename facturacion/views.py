"""
Vistas para el sistema de facturación.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from decimal import Decimal
import json

# Importar modelos de Oscar
try:
    from oscar.apps.catalogue.models import Product
except ImportError:
    Product = None

# Importar modelos propios
from .models import Factura, DetalleFactura

User = get_user_model()


@login_required
def facturacion_index(request):
    """
    Vista principal del módulo de facturación.
    Muestra la interfaz para generar facturas.
    """
    return render(request, 'facturacion/index.html')


@login_required
@require_GET
def listar_clientes_ajax(request):
    """
    Lista todos los usuarios con rol CLIENTE para el Select2.
    Soporta búsqueda por nombre, email o NIT.
    """
    try:
        # Obtener parámetro de búsqueda de Select2
        search = request.GET.get('q', '').strip()
        
        # Filtrar solo usuarios con rol CLIENTE (usar string directamente)
        clientes = User.objects.filter(rol='CLIENTE', activo=True, is_active=True)
        
        # Log para debugging
        print(f"[DEBUG] Búsqueda: '{search}'")
        print(f"[DEBUG] Total clientes activos: {clientes.count()}")
        
        # Aplicar búsqueda si existe
        if search:
            clientes = clientes.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search)  # username será el NIT
            )
            print(f"[DEBUG] Clientes después de filtro búsqueda: {clientes.count()}")
        
        # Preparar resultados para Select2
        results = []
        for cliente in clientes[:20]:  # Limitar a 20 resultados
            result_item = {
                'id': cliente.id,
                'text': f"{cliente.get_full_name() or cliente.username} - {cliente.email}",
                'nombre': cliente.get_full_name(),
                'nit': cliente.username,
                'email': cliente.email,
                'telefono': cliente.telefono or '',
                'direccion': cliente.direccion or '',
            }
            results.append(result_item)
            print(f"[DEBUG] Cliente agregado: {result_item}")
        
        print(f"[DEBUG] Total resultados a enviar: {len(results)}")
        
        response_data = {
            'results': results,
            'pagination': {'more': False}
        }
        
        print(f"[DEBUG] Response JSON: {response_data}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def crear_cliente_ajax(request):
    """
    Crea un nuevo cliente (User con rol CLIENTE) mediante AJAX.
    Los datos vienen del modal de SweetAlert2.
    """
    try:
        # Parsear datos JSON del body
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['nombre_completo', 'nit', 'email']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'El campo {field} es requerido'
                }, status=400)
        
        # Validar que el NIT no exista
        if User.objects.filter(username=data['nit']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Ya existe un cliente con este NIT'
            }, status=400)
        
        # Validar que el email no exista
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Ya existe un cliente con este correo electrónico'
            }, status=400)
        
        # Dividir nombre completo en first_name y last_name
        nombre_completo = data['nombre_completo'].strip()
        nombre_parts = nombre_completo.split(' ', 1)
        first_name = nombre_parts[0]
        last_name = nombre_parts[1] if len(nombre_parts) > 1 else ''
        
        # Crear el cliente con transacción
        with transaction.atomic():
            cliente = User.objects.create_user(
                username=data['nit'],  # NIT como username
                email=data['email'],
                first_name=first_name,
                last_name=last_name,
                rol=User.RoleChoices.CLIENTE,
                telefono=data.get('telefono', ''),
                direccion=data.get('direccion', ''),
                password=data['nit'],  # Contraseña = NIT/Cédula (se cifra automáticamente)
                activo=True,
                is_active=True,
            )
            
            # Asignar permisos de cliente automáticamente
            cliente.asignar_permisos_por_rol()
        
        # Retornar datos del cliente creado para Select2
        return JsonResponse({
            'success': True,
            'message': 'Cliente creado exitosamente',
            'cliente': {
                'id': cliente.id,
                'text': f"{cliente.get_full_name()} - {cliente.email}",
                'nombre': cliente.get_full_name(),
                'nit': cliente.username,
                'email': cliente.email,
                'telefono': cliente.telefono or '',
                'direccion': cliente.direccion or '',
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al crear cliente: {str(e)}'
        }, status=500)


@login_required
@require_GET
def buscar_productos_ajax(request):
    """
    Busca productos del catálogo de Django Oscar por título o UPC.
    Retorna un JSON compatible con Select2.
    """
    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = 20
    
    if not query or len(query) < 2:
        return JsonResponse({
            'results': [],
            'pagination': {'more': False}
        })
    
    try:
        if Product:
            # Buscar en productos de Oscar
            productos = Product.objects.filter(
                Q(title__icontains=query) | Q(upc__icontains=query)
            ).distinct()[:page_size]
            
            results = []
            for producto in productos:
                # Obtener precio del producto
                precio = Decimal('0.00')
                if hasattr(producto, 'stockrecords') and producto.stockrecords.exists():
                    stockrecord = producto.stockrecords.first()
                    if stockrecord.price:
                        precio = stockrecord.price
                
                results.append({
                    'id': producto.id,
                    'text': producto.title,
                    'upc': producto.upc or '',
                    'precio': str(precio),
                    'descripcion': producto.description or producto.title,
                })
            
            return JsonResponse({
                'results': results,
                'pagination': {'more': False}
            })
        else:
            # Oscar no está instalado o configurado
            return JsonResponse({
                'results': [],
                'pagination': {'more': False},
                'message': 'Catálogo de productos no disponible'
            })
            
    except Exception as e:
        return JsonResponse({
            'results': [],
            'pagination': {'more': False},
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def guardar_factura_ajax(request):
    """
    Guarda una factura completa con todos sus detalles.
    Recibe un JSON con:
    - cliente_id
    - detalles: [{ descripcion, cantidad, precio_unitario, descuento }]
    - metodo_pago
    - condicion_pago
    - notas
    """
    try:
        data = json.loads(request.body)
        
        # Validar cliente
        cliente_id = data.get('cliente_id')
        if not cliente_id:
            return JsonResponse({
                'success': False,
                'message': 'Debe seleccionar un cliente'
            }, status=400)
        
        cliente = User.objects.get(id=cliente_id, rol='CLIENTE')
        
        # Validar detalles
        detalles = data.get('detalles', [])
        if not detalles or len(detalles) == 0:
            return JsonResponse({
                'success': False,
                'message': 'Debe agregar al menos un producto a la factura'
            }, status=400)
        
        # Obtener datos de pago
        metodo_pago = data.get('metodo_pago', 'EFECTIVO')
        condicion_pago = data.get('condicion_pago', 'CONTADO')
        notas = data.get('notas', '')
        
        # Crear factura con transacción atómica
        with transaction.atomic():
            # Crear la factura (el código se genera automáticamente)
            factura = Factura.objects.create(
                cliente=cliente,
                usuario_emisor=request.user,
                metodo_pago=metodo_pago,
                condicion_pago=condicion_pago,
                notas=notas,
                fecha_emision=timezone.now(),
            )
            
            # Crear los detalles
            subtotal = Decimal('0.00')
            total_descuentos = Decimal('0.00')
            
            for i, detalle_data in enumerate(detalles):
                cantidad = Decimal(str(detalle_data.get('cantidad', 1)))
                precio_unitario = Decimal(str(detalle_data.get('precio_unitario', 0)))
                descuento = Decimal(str(detalle_data.get('descuento', 0)))
                descripcion = detalle_data.get('descripcion', '')
                producto_oscar_id = detalle_data.get('producto_id', None)
                
                # Crear detalle (los cálculos se hacen automáticamente en el modelo)
                detalle = DetalleFactura.objects.create(
                    factura=factura,
                    descripcion=descripcion,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento=descuento,
                    producto_oscar_id=producto_oscar_id,
                    orden=i + 1
                )
                
                # Acumular totales
                subtotal += detalle.precio_unitario * cantidad
                total_descuentos += descuento * cantidad
            
            # Calcular subtotal neto e IVA
            subtotal_neto = subtotal - total_descuentos
            total_iva = subtotal_neto * Decimal('0.19')  # IVA 19%
            total_pagar = subtotal_neto + total_iva
            
            # Actualizar factura con totales
            factura.subtotal = subtotal
            factura.total_descuentos = total_descuentos
            factura.subtotal_neto = subtotal_neto
            factura.total_iva = total_iva
            factura.total_pagar = total_pagar
            factura.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Factura generada exitosamente',
                'factura': {
                    'id': factura.id,
                    'codigo_factura': factura.codigo_factura,
                    'total_pagar': str(factura.total_pagar),
                    'fecha_emision': factura.fecha_emision.strftime('%d/%m/%Y %H:%M'),
                }
            })
            
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar la factura: {str(e)}'
        }, status=500)
