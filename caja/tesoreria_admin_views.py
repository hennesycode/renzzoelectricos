"""
Vistas administrativas para gestión avanzada de tesorería.
Solo accesible por superusuarios.
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
import logging

from .tesoreria_admin_forms import TransaccionTesoreriaAdminForm, GestorTesoreriaAdminForm
from .models import TipoMovimiento, Cuenta, TransaccionGeneral
# Importaciones básicas - las funciones específicas se implementarán cuando sea necesario

logger = logging.getLogger(__name__)


def es_superusuario(user):
    """Verifica que el usuario sea superusuario."""
    return user.is_superuser


@user_passes_test(es_superusuario)
def transaccion_tesoreria_admin(request):
    """
    Vista para crear transacciones individuales de tesorería
    con fecha personalizada.
    """
    if request.method == 'POST':
        form = TransaccionTesoreriaAdminForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    datos = form.cleaned_data
                    
                    # Crear la transacción usando la función existente
                    # Crear TransaccionGeneral directamente
                    from .models import TransaccionGeneral
                    
                    transaccion = TransaccionGeneral.objects.create(
                        cuenta=datos['cuenta'],
                        tipo_movimiento=datos['tipo_movimiento'],
                        monto=datos['monto'],
                        descripcion=datos['descripcion'],
                        es_ingreso=(datos['tipo'] == 'INGRESO'),
                        usuario=datos['usuario'],
                        fecha_creacion=datos['fecha']
                    )
                    
                    tipo_texto = 'Transferencia' if datos['tipo'] == 'TRANSFERENCIA' else ('Ingreso' if datos['tipo'] == 'INGRESO' else 'Egreso')
                    mensaje = f"{tipo_texto} de ${datos['monto']:,.2f} creado exitosamente"
                    
                    messages.success(request, mensaje)
                    logger.info(f"Transacción creada por admin: {request.user.username} - {mensaje}")
                    
                    # Redirigir para evitar reenvío del formulario
                    return redirect('caja:transaccion_tesoreria_admin')
                    
            except Exception as e:
                logger.error(f"Error creando transacción admin: {str(e)}")
                messages.error(request, f"Error al crear la transacción: {str(e)}")
    else:
        # Valores iniciales
        form = TransaccionTesoreriaAdminForm(initial={
            'fecha': timezone.now(),
            'usuario': request.user
        })
    
    context = {
        'form': form,
        'title': 'Crear Transacción de Tesorería',
        'subtitle': 'Transacciones individuales con fecha personalizada'
    }
    
    return render(request, 'admin/caja/transaccion_tesoreria_admin.html', context)


@user_passes_test(es_superusuario)
def gestor_tesoreria_admin(request):
    """
    Vista para gestionar múltiples operaciones de tesorería
    con fecha personalizada.
    """
    if request.method == 'POST':
        form = GestorTesoreriaAdminForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    datos = form.cleaned_data
                    transacciones_data = form.get_transacciones_data()
                    
                    if not transacciones_data:
                        messages.warning(request, "No se especificaron transacciones para crear")
                        return redirect('caja:gestor_tesoreria_admin')
                    
                    transacciones_creadas = []
                    total_procesado = Decimal('0.00')
                    
                    # Crear cada transacción directamente
                    for trans_data in transacciones_data:
                        # Obtener o crear tipo de movimiento
                        tipo_mov, created = TipoMovimiento.objects.get_or_create(
                            codigo=trans_data['tipo_codigo'],
                            defaults={
                                'nombre': trans_data['tipo_nombre'],
                                'tipo_base': 'GASTO' if trans_data['tipo'] == 'EGRESO' else trans_data['tipo'],
                                'activo': True
                            }
                        )
                        
                        # Crear transacción directamente
                        TransaccionGeneral.objects.create(
                            cuenta=trans_data['cuenta'],
                            tipo_movimiento=tipo_mov,
                            monto=trans_data['monto'],
                            descripcion=trans_data['descripcion'],
                            es_ingreso=(trans_data['tipo'] == 'INGRESO'),
                            usuario=datos['usuario'],
                            fecha_creacion=datos['fecha_base']
                        )
                        
                        tipo_texto = 'Transferencia' if trans_data['tipo'] == 'TRANSFERENCIA' else ('Ingreso' if trans_data['tipo'] == 'INGRESO' else 'Egreso')
                        transacciones_creadas.append(f"{tipo_texto}: ${trans_data['monto']:,.2f}")
                        total_procesado += trans_data['monto']
                    
                    # Mensaje de éxito
                    mensaje = f"Se crearon {len(transacciones_creadas)} transacciones por un total de ${total_procesado:,.2f}"
                    messages.success(request, mensaje)
                    logger.info(f"Transacciones masivas creadas por admin: {request.user.username} - {mensaje}")
                    
                    # Redirigir para evitar reenvío del formulario
                    return redirect('caja:gestor_tesoreria_admin')
                    
            except Exception as e:
                logger.error(f"Error creando transacciones masivas admin: {str(e)}")
                messages.error(request, f"Error al crear las transacciones: {str(e)}")
    else:
        # Valores iniciales
        form = GestorTesoreriaAdminForm(initial={
            'fecha_base': timezone.now(),
            'usuario': request.user
        })
    
    # Obtener estadísticas actuales
    estadisticas = obtener_estadisticas_tesoreria()
    
    context = {
        'form': form,
        'estadisticas': estadisticas,
        'title': 'Gestor de Tesorería Avanzado',
        'subtitle': 'Gestión masiva de transacciones con fecha personalizada'
    }
    
    return render(request, 'admin/caja/gestor_tesoreria_admin.html', context)


@user_passes_test(es_superusuario)
def ajax_validar_fondos(request):
    """
    Vista AJAX para validar fondos disponibles en una cuenta.
    """
    if request.method == 'GET':
        cuenta_id = request.GET.get('cuenta_id')
        monto = request.GET.get('monto', '0')
        
        try:
            cuenta = Cuenta.objects.get(id=cuenta_id)
            monto_decimal = Decimal(monto)
            
            tiene_fondos = cuenta.tiene_fondos_suficientes(monto_decimal)
            
            return JsonResponse({
                'tiene_fondos': tiene_fondos,
                'saldo_actual': float(cuenta.saldo_actual),
                'saldo_formateado': f"${cuenta.saldo_actual:,.2f}",
                'cuenta_nombre': cuenta.nombre
            })
            
        except (Cuenta.DoesNotExist, ValueError, TypeError) as e:
            return JsonResponse({
                'error': f'Error validando fondos: {str(e)}'
            }, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def obtener_estadisticas_tesoreria():
    """
    Obtiene estadísticas actuales de tesorería para mostrar en el admin.
    """
    try:
        cuentas = Cuenta.objects.filter(activo=True)
        
        estadisticas = {
            'cuentas': [],
            'total_activos': Decimal('0.00'),
            'total_transacciones_hoy': 0
        }
        
        hoy = timezone.now().date()
        
        for cuenta in cuentas:
            saldo = cuenta.saldo_actual
            transacciones_hoy = TransaccionGeneral.objects.filter(
                cuenta=cuenta,
                fecha_creacion__date=hoy
            ).count()
            
            estadisticas['cuentas'].append({
                'nombre': cuenta.nombre,
                'tipo': cuenta.get_tipo_display(),
                'saldo': saldo,
                'saldo_formateado': f"${saldo:,.2f}",
                'transacciones_hoy': transacciones_hoy
            })
            
            estadisticas['total_activos'] += saldo
            estadisticas['total_transacciones_hoy'] += transacciones_hoy
        
        estadisticas['total_activos_formateado'] = f"${estadisticas['total_activos']:,.2f}"
        
        return estadisticas
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas tesorería: {str(e)}")
        return {
            'cuentas': [],
            'total_activos': Decimal('0.00'),
            'total_activos_formateado': '$0.00',
            'total_transacciones_hoy': 0,
            'error': f'Error cargando estadísticas: {str(e)}'
        }