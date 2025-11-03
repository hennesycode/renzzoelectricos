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
import json

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
        
        # Filtrar solo usuarios con rol CLIENTE
        clientes = User.objects.filter(rol=User.RoleChoices.CLIENTE, activo=True)
        
        # Aplicar búsqueda si existe
        if search:
            clientes = clientes.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search)  # username será el NIT
            )
        
        # Preparar resultados para Select2
        results = []
        for cliente in clientes[:20]:  # Limitar a 20 resultados
            results.append({
                'id': cliente.id,
                'text': f"{cliente.get_full_name() or cliente.username} - {cliente.email}",
                'nombre': cliente.get_full_name(),
                'nit': cliente.username,
                'email': cliente.email,
                'telefono': cliente.telefono or '',
                'direccion': cliente.direccion or '',
            })
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': False}
        })
        
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
