"""
Vistas para el sistema de caja registradora.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    DenominacionMoneda, ConteoEfectivo, DetalleConteo
)


@login_required
@permission_required('users.can_view_caja', raise_exception=True)
def caja_dashboard(request):
    """
    Dashboard principal del sistema de caja.
    Muestra la caja global única (si existe y está abierta).
    """
    # Obtener la caja abierta del sistema (única y global)
    caja_actual = CajaRegistradora.objects.filter(
        estado='ABIERTA'
    ).first()
    
    # SIEMPRE mostrar las estadísticas (si no hay caja abierta, todo en ceros)
    total_ingresos = Decimal('0.00')
    total_egresos = Decimal('0.00')
    total_disponible = Decimal('0.00')
    ultimos_movimientos = []
    
    if caja_actual:
        # Si hay caja abierta, calcular movimientos de ESA caja específica
        movimientos_caja = MovimientoCaja.objects.filter(caja=caja_actual)
        
        # Excluir el movimiento de apertura del cálculo de ingresos
        # para no duplicar el monto inicial
        total_ingresos = movimientos_caja.filter(
            tipo='INGRESO'
        ).exclude(
            tipo_movimiento__codigo='APERTURA'
        ).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        total_egresos = movimientos_caja.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Total disponible = monto inicial + ingresos (sin apertura) - egresos
        total_disponible = caja_actual.monto_inicial + total_ingresos - total_egresos
        
        # Mostrar TODOS los movimientos de la caja abierta (incluyendo apertura)
        ultimos_movimientos = movimientos_caja.select_related(
            'tipo_movimiento', 'caja', 'usuario'
        ).order_by('-fecha_movimiento')[:50]
    
    estadisticas = {
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'numero_movimientos': len(ultimos_movimientos),
        'total_disponible': total_disponible,
    }
    
    context = {
        'caja_actual': caja_actual,
        'estadisticas': estadisticas,
        'ultimos_movimientos': ultimos_movimientos,
    }
    
    return render(request, 'caja/dashboard.html', context)


@login_required
@permission_required('users.can_manage_caja', raise_exception=True)
def abrir_caja(request):
    """
    Vista para abrir una nueva caja (ÚNICA Y GLOBAL para todo el sistema).
    Solo puede existir UNA caja abierta a la vez.
    SOLO funciona vía AJAX - desde el modal en dashboard.
    """
    # Verificar si ya hay una caja abierta en el sistema (GLOBAL)
    caja_abierta = CajaRegistradora.objects.filter(
        estado='ABIERTA'
    ).exists()
    
    if caja_abierta:
        is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({
                'success': False, 
                'error': 'Ya existe una caja abierta en el sistema. Ciérrala antes de abrir una nueva.'
            }, status=400)
        messages.error(request, _('Ya existe una caja abierta en el sistema. Ciérrala antes de abrir una nueva.'))
        return redirect('caja:dashboard')
    
    # Solo aceptar peticiones AJAX POST
    if request.method != 'POST':
        return redirect('caja:dashboard')
    
    is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not is_ajax:
        return redirect('caja:dashboard')
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Payload inválido'}, status=400)

    monto_inicial = payload.get('monto_inicial')
    observaciones = payload.get('observaciones', '')
    conteos = payload.get('conteos', {})

    try:
        total_calculado = None
        if conteos:
            total = Decimal('0.00')
            for denom_id, cantidad in conteos.items():
                try:
                    denom = DenominacionMoneda.objects.get(id=int(denom_id))
                    cantidad = int(cantidad)
                    if cantidad <= 0:
                        continue
                    subtotal = denom.valor * Decimal(cantidad)
                    total += subtotal
                except DenominacionMoneda.DoesNotExist:
                    continue
            total_calculado = total

        if monto_inicial is None or monto_inicial == '':
            if total_calculado is None:
                return JsonResponse({'success': False, 'error': 'Monto inicial o conteos requeridos'}, status=400)
            monto_inicial = total_calculado

        monto_inicial = Decimal(monto_inicial)
        if monto_inicial < 0:
            raise ValueError('El monto no puede ser negativo')

        # Usar transacción atómica para asegurar que caja y movimiento se crean juntos
        with transaction.atomic():
            # Crear caja ÚNICA GLOBAL (el cajero es quien la abre)
            caja = CajaRegistradora.objects.create(
                cajero=request.user,
                monto_inicial=monto_inicial,
                observaciones_apertura=observaciones
            )

            # Si hay conteos, crear ConteoEfectivo DE APERTURA
            if conteos:
                conteo = ConteoEfectivo.objects.create(
                    caja=caja,
                    tipo_conteo='APERTURA',
                    usuario=request.user,
                    total=monto_inicial
                )
                for denom_id, cantidad in conteos.items():
                    try:
                        denom = DenominacionMoneda.objects.get(id=int(denom_id))
                        cantidad = int(cantidad)
                        if cantidad <= 0:
                            continue
                        subtotal = denom.valor * Decimal(cantidad)
                        DetalleConteo.objects.create(
                            conteo=conteo,
                            denominacion=denom,
                            cantidad=cantidad,
                            subtotal=subtotal
                        )
                    except DenominacionMoneda.DoesNotExist:
                        continue

            # NO CREAR movimiento de apertura porque monto_inicial ya representa ese valor
            # El cálculo es: monto_inicial + ingresos - egresos
            # Si creamos un movimiento INGRESO por monto_inicial, estaríamos duplicando

        # Preparar mensaje de éxito
        monto_formateado = f'${monto_inicial:,.0f}'
        msg = f'Caja abierta exitosamente con {monto_formateado}'
        
        # Obtener nombre del cajero de forma segura
        cajero_nombre = str(caja.cajero.username)
        try:
            full_name = caja.cajero.get_full_name()
            if full_name and full_name.strip():
                cajero_nombre = full_name
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'message': msg,
            'caja': {
                'id': caja.id,
                'monto_inicial': float(caja.monto_inicial),
                'fecha_apertura': caja.fecha_apertura.isoformat(),
                'cajero': cajero_nombre,
            }
        })
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': f'Monto inicial inválido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al abrir caja: {str(e)}'}, status=500)


@login_required
@permission_required('users.can_manage_caja', raise_exception=True)
def cerrar_caja(request):
    """
    Vista para cerrar la caja actual del sistema (ÚNICA Y GLOBAL).
    SOLO funciona vía AJAX - desde el modal en dashboard.
    """
    # Obtener la caja abierta del sistema (GLOBAL)
    try:
        caja = CajaRegistradora.objects.get(estado='ABIERTA')
    except CajaRegistradora.DoesNotExist:
        is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'No hay ninguna caja abierta en el sistema'}, status=400)
        messages.error(request, _('No hay ninguna caja abierta en el sistema'))
        return redirect('caja:dashboard')
    
    # Solo aceptar peticiones AJAX POST
    if request.method != 'POST':
        return redirect('caja:dashboard')
    
    is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not is_ajax:
        return redirect('caja:dashboard')
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Payload inválido'}, status=400)

    monto_declarado = payload.get('monto_declarado', '0')
    observaciones = payload.get('observaciones', '')
    conteos = payload.get('conteos', {})

    try:
        monto_declarado = Decimal(monto_declarado)
        if monto_declarado < 0:
            raise ValueError('El monto no puede ser negativo')

        # Crear registro de ConteoEfectivo DE CIERRE
        conteo = ConteoEfectivo.objects.create(
            caja=caja,
            tipo_conteo='CIERRE',
            usuario=request.user,
            total=monto_declarado
        )

        # Crear detalles
        for denom_id, cantidad in conteos.items():
            try:
                denom = DenominacionMoneda.objects.get(id=int(denom_id))
                cantidad = int(cantidad)
                if cantidad <= 0:
                    continue
                subtotal = denom.valor * Decimal(cantidad)
                DetalleConteo.objects.create(
                    conteo=conteo,
                    denominacion=denom,
                    cantidad=cantidad,
                    subtotal=subtotal
                )
            except DenominacionMoneda.DoesNotExist:
                continue

        # Cerrar caja (actualiza monto_final_declarado, diferencia, estado)
        diferencia = caja.cerrar_caja(monto_declarado, observaciones)

        return JsonResponse({
            'success': True,
            'message': 'Caja cerrada exitosamente',
            'diferencia': float(diferencia),
            'monto_final_declarado': float(caja.monto_final_declarado),
            'monto_final_sistema': float(caja.monto_final_sistema),
        })
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Monto declarado inválido'}, status=400)


@login_required
@permission_required('users.can_view_caja', raise_exception=True)
def nuevo_movimiento(request):
    """
    Vista para registrar un nuevo movimiento de caja.
    Registra movimientos en la caja global del sistema.
    SOLO funciona vía AJAX - desde el modal en dashboard.
    """
    # Verificar que hay una caja abierta en el sistema (GLOBAL)
    caja = CajaRegistradora.objects.filter(
        estado='ABIERTA'
    ).first()
    
    if not caja:
        is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'No hay una caja abierta en el sistema'}, status=400)
        messages.error(request, _('No hay una caja abierta en el sistema. Abre una caja primero.'))
        return redirect('caja:dashboard')
    
    # Solo aceptar peticiones AJAX POST
    if request.method != 'POST':
        return redirect('caja:dashboard')
    
    is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not is_ajax:
        return redirect('caja:dashboard')
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Payload inválido'}, status=400)

    tipo = payload.get('tipo')
    tipo_movimiento_id = payload.get('tipo_movimiento')
    monto = payload.get('monto', '0')
    descripcion = payload.get('descripcion', '')
    referencia = payload.get('referencia', '')

    try:
        monto = Decimal(monto)
        if monto <= 0:
            raise ValueError('El monto debe ser mayor a cero')

        tipo_movimiento = get_object_or_404(TipoMovimiento, id=tipo_movimiento_id)

        movimiento = MovimientoCaja.objects.create(
            caja=caja,
            tipo=tipo,
            tipo_movimiento=tipo_movimiento,
            usuario=request.user,
            monto=monto,
            descripcion=descripcion,
            referencia=referencia
        )

        return JsonResponse({
            'success': True,
            'message': 'Movimiento registrado exitosamente',
            'movimiento': {
                'id': movimiento.id,
                'fecha': movimiento.fecha_movimiento.isoformat(),
                'tipo': movimiento.tipo,
                'monto': float(movimiento.monto),
                'descripcion': movimiento.descripcion,
            }
        })
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


class CajaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Lista de todas las cajas (historial).
    Muestra todas las cajas del sistema (global).
    """
    model = CajaRegistradora
    template_name = 'caja/historial.html'
    context_object_name = 'cajas'
    paginate_by = 20
    permission_required = 'users.can_view_caja'
    
    def get_queryset(self):
        # Mostrar todas las cajas del sistema (ya no filtramos por usuario)
        return CajaRegistradora.objects.select_related('cajero').order_by('-fecha_apertura')


class CajaDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detalle de una caja específica con todos sus movimientos.
    Cualquier usuario con permisos puede ver cualquier caja (sistema global).
    """
    model = CajaRegistradora
    template_name = 'caja/detalle.html'
    context_object_name = 'caja'
    permission_required = 'users.can_view_caja'
    
    def get_queryset(self):
        # Todas las cajas son visibles (sistema global)
        return CajaRegistradora.objects.prefetch_related('movimientos__tipo_movimiento', 'movimientos__usuario')


@login_required
@permission_required('users.can_manage_caja', raise_exception=True)
def contar_efectivo(request):
    """
    Vista AJAX para el conteo de efectivo con denominaciones.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        conteos = data.get('conteos', {})
        
        total = Decimal('0.00')
        detalles = []
        
        for denominacion_id, cantidad in conteos.items():
            if cantidad > 0:
                denominacion = get_object_or_404(DenominacionMoneda, id=denominacion_id)
                subtotal = denominacion.valor * Decimal(str(cantidad))
                total += subtotal
                
                detalles.append({
                    'denominacion': str(denominacion),
                    'cantidad': cantidad,
                    'subtotal': float(subtotal),
                    'valor_unitario': float(denominacion.valor)
                })
        
        return JsonResponse({
            'success': True,
            'total': float(total),
            'detalles': detalles
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error en el conteo: {str(e)}'
        }, status=400)


@login_required
@permission_required('users.can_view_caja', raise_exception=True)
def obtener_denominaciones(request):
    """Devuelve las denominaciones activas en JSON para construir el modal de conteo."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    denoms = DenominacionMoneda.objects.filter(activo=True).order_by('-valor')
    data = [
        {
            'id': d.id,
            'valor': float(d.valor),
            'tipo': d.tipo,
            'label': str(d)
        }
        for d in denoms
    ]
    return JsonResponse({'success': True, 'denominaciones': data})


@login_required
@permission_required('users.can_view_caja', raise_exception=True)
def obtener_estado_caja(request):
    """
    Devuelve el estado actual de la caja abierta con:
    - Total disponible (calculado)
    - Denominaciones esperadas (cálculo automático)
    - Monto inicial
    - Total ingresos y egresos
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        caja = CajaRegistradora.objects.get(estado='ABIERTA')
    except CajaRegistradora.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No hay una caja abierta'}, status=400)
    
    # Calcular totales
    movimientos = MovimientoCaja.objects.filter(caja=caja)
    
    total_ingresos = movimientos.filter(
        tipo='INGRESO'
    ).exclude(
        tipo_movimiento__codigo='APERTURA'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    total_egresos = movimientos.filter(
        tipo='EGRESO'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    total_disponible = caja.monto_inicial + total_ingresos - total_egresos
    
    # Calcular denominaciones esperadas (distribución óptima)
    # Este es un cálculo aproximado - en la realidad el efectivo puede variar
    denominaciones_esperadas = calcular_denominaciones_esperadas(total_disponible)
    
    return JsonResponse({
        'success': True,
        'caja_id': caja.id,
        'monto_inicial': float(caja.monto_inicial),
        'total_ingresos': float(total_ingresos),
        'total_egresos': float(total_egresos),
        'total_disponible': float(total_disponible),
        'denominaciones_esperadas': denominaciones_esperadas
    })


def calcular_denominaciones_esperadas(total):
    """
    Calcula una distribución aproximada de denominaciones para el total dado.
    Usa un algoritmo greedy para distribuir el dinero.
    """
    from decimal import Decimal
    
    # Obtener denominaciones ordenadas de mayor a menor
    denoms = DenominacionMoneda.objects.filter(activo=True).order_by('-valor')
    
    resultado = {}
    resto = Decimal(str(total))
    
    for denom in denoms:
        if resto >= denom.valor:
            cantidad = int(resto / denom.valor)
            resultado[str(denom.id)] = cantidad
            resto = resto - (denom.valor * cantidad)
        else:
            resultado[str(denom.id)] = 0
    
    return resultado


@login_required
@permission_required('users.can_view_caja', raise_exception=True)
def obtener_tipos_movimiento(request):
    """
    Devuelve los tipos de movimiento activos filtrados por tipo (INGRESO/EGRESO).
    Para INGRESO solo devuelve: AJUSTE, CAMBIO, DEVOL, INGRESO, VENTA
    Para EGRESO devuelve: GASTO, PAGO, RETIRO
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    # Obtener el tipo de movimiento solicitado (INGRESO o EGRESO)
    tipo_filtro = request.GET.get('tipo', '').upper()
    
    # Definir códigos permitidos por tipo
    CODIGOS_INGRESO = ['AJUSTE', 'CAMBIO', 'DEVOL', 'INGRESO', 'VENTA']
    CODIGOS_EGRESO = ['GASTO', 'PAGO', 'RETIRO']
    
    # Filtrar tipos según el parámetro
    if tipo_filtro == 'INGRESO':
        tipos = TipoMovimiento.objects.filter(activo=True, codigo__in=CODIGOS_INGRESO)
    elif tipo_filtro == 'EGRESO':
        tipos = TipoMovimiento.objects.filter(activo=True, codigo__in=CODIGOS_EGRESO)
    else:
        # Si no se especifica tipo, devolver todos los activos (excepto APERTURA)
        tipos = TipoMovimiento.objects.filter(activo=True).exclude(codigo='APERTURA')
    
    data = [
        {'id': t.id, 'nombre': t.nombre, 'codigo': t.codigo}
        for t in tipos.order_by('nombre')
    ]
    return JsonResponse({'success': True, 'tipos': data})
