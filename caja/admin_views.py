"""
Vistas administrativas avanzadas para el sistema de caja.
Solo accesibles por superusuarios.
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime

from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    Cuenta, TransaccionGeneral
)
from .admin_forms import CajaAdminCompleteForm


def superuser_required(view_func):
    """Decorador que requiere que el usuario sea superusuario."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("Solo los superusuarios pueden acceder a esta función.")
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_member_required
@superuser_required
def crear_caja_completa_admin(request):
    """
    Vista para crear una caja completa con fecha personalizada y movimientos.
    Solo accesible por superusuarios desde el admin.
    """
    if request.method == 'POST':
        form = CajaAdminCompleteForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear la caja con los datos del formulario
                    caja_data = form.cleaned_data
                    
                    # 1. CREAR LA CAJA
                    caja = CajaRegistradora(
                        cajero=caja_data['cajero'],
                        monto_inicial=caja_data['monto_inicial'],
                        observaciones_apertura=caja_data['observaciones_apertura'],
                        estado='ABIERTA'
                    )
                    
                    # Establecer fecha personalizada ANTES de guardar
                    # para evitar que auto_now_add la sobrescriba
                    caja.fecha_apertura = caja_data['fecha_apertura']
                    caja.save()
                    
                    # 2. CREAR MOVIMIENTOS ADICIONALES (las señales ya crearon la apertura)
                    movimientos_data = form.get_movimientos_data()
                    
                    for mov_data in movimientos_data:
                        if mov_data['monto'] > 0:
                            # Obtener o crear tipo de movimiento
                            tipo_movimiento, _ = TipoMovimiento.objects.get_or_create(
                                codigo=mov_data['tipo_codigo'],
                                defaults={
                                    'nombre': mov_data['tipo_nombre'],
                                    'activo': True,
                                    'tipo_base': TipoMovimiento.TipoBaseChoices.INGRESO if mov_data['tipo'] == 'INGRESO' else TipoMovimiento.TipoBaseChoices.GASTO
                                }
                            )
                            
                            # Crear movimiento (la señal creará automáticamente la transacción)
                            movimiento = MovimientoCaja.objects.create(
                                caja=caja,
                                tipo_movimiento=tipo_movimiento,
                                tipo=mov_data['tipo'],
                                monto=mov_data['monto'],
                                descripcion=mov_data['descripcion'],
                                referencia=mov_data['referencia'],
                                usuario=request.user
                            )
                            
                            # Actualizar fecha del movimiento manualmente
                            # (usando la misma fecha de apertura + algunos minutos)
                            movimiento.fecha_movimiento = caja_data['fecha_apertura']
                            movimiento.save(update_fields=['fecha_movimiento'])
                    
                    # 3. CERRAR LA CAJA SI SE SOLICITA
                    if caja_data['cerrar_caja']:
                        fecha_cierre = caja_data.get('fecha_cierre') or timezone.now()
                        
                        # Usar el método existente de cerrar caja para mantener consistencia
                        diferencia = caja.cerrar_caja(
                            monto_final_declarado=caja_data['monto_final_declarado'],
                            observaciones_cierre=caja_data['observaciones_cierre']
                        )
                        
                        # Actualizar fecha de cierre personalizada
                        caja.fecha_cierre = fecha_cierre
                        
                        # Agregar distribución del dinero
                        caja.dinero_en_caja = caja_data['dinero_en_caja']
                        caja.dinero_guardado = caja_data['dinero_guardado']
                        
                        caja.save()
                    
                    messages.success(
                        request, 
                        f'✅ Caja #{caja.id} creada exitosamente para {caja.cajero.username}. '
                        f'Estado: {caja.get_estado_display()}'
                    )
                    
                    # Redirect al admin de cajas
                    return redirect('admin:caja_cajaregistradora_changelist')
                    
            except Exception as e:
                messages.error(request, f'❌ Error al crear la caja: {str(e)}')
    else:
        # Valores iniciales para el formulario
        initial_data = {
            'fecha_apertura': timezone.now().replace(second=0, microsecond=0),
            'fecha_cierre': timezone.now().replace(second=0, microsecond=0) + timezone.timedelta(hours=8),
            'cajero': request.user,
        }
        form = CajaAdminCompleteForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Crear Caja Completa con Fecha Personalizada',
        'subtitle': 'Administración Avanzada - Solo Superusuarios',
        'opts': CajaRegistradora._meta,
        'has_view_permission': True,
        'has_change_permission': True,
    }
    
    return render(request, 'admin/caja/crear_caja_completa.html', context)


@staff_member_required
@superuser_required
def resumen_caja_admin(request, caja_id):
    """
    Vista de resumen detallado de una caja para superusuarios.
    Muestra información completa incluyendo transacciones de tesorería.
    """
    try:
        caja = CajaRegistradora.objects.get(id=caja_id)
    except CajaRegistradora.DoesNotExist:
        messages.error(request, 'La caja especificada no existe.')
        return redirect('admin:caja_cajaregistradora_changelist')
    
    # Obtener todos los movimientos de la caja
    movimientos = MovimientoCaja.objects.filter(caja=caja).order_by('fecha_movimiento')
    
    # Obtener transacciones de tesorería asociadas
    transacciones = TransaccionGeneral.objects.filter(
        movimiento_caja_asociado__caja=caja
    ).order_by('fecha')
    
    # Calcular totales
    total_ingresos = sum(m.monto for m in movimientos if m.tipo == 'INGRESO')
    total_egresos = sum(m.monto for m in movimientos if m.tipo == 'EGRESO')
    total_entradas_banco = sum(
        m.monto for m in movimientos 
        if m.tipo == 'INGRESO' and '[BANCO]' in m.descripcion
    )
    
    # Separar movimientos por tipo
    movimientos_apertura = movimientos.filter(tipo_movimiento__codigo='APERTURA')
    movimientos_ingresos = movimientos.filter(tipo='INGRESO').exclude(tipo_movimiento__codigo='APERTURA')
    movimientos_egresos = movimientos.filter(tipo='EGRESO')
    
    context = {
        'caja': caja,
        'movimientos': movimientos,
        'movimientos_apertura': movimientos_apertura,
        'movimientos_ingresos': movimientos_ingresos,
        'movimientos_egresos': movimientos_egresos,
        'transacciones': transacciones,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'total_entradas_banco': total_entradas_banco,
        'title': f'Resumen Detallado - Caja #{caja.id}',
        'opts': CajaRegistradora._meta,
        'has_view_permission': True,
        'has_change_permission': True,
    }
    
    return render(request, 'admin/caja/resumen_caja_detallado.html', context)