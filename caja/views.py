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
from django.db.models import Sum, Q, Count, Avg
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    DenominacionMoneda, ConteoEfectivo, DetalleConteo
)
from .decorators import staff_or_permission_required


@staff_or_permission_required('users.can_view_caja')
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


@staff_or_permission_required('users.can_manage_caja')
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


@staff_or_permission_required('users.can_manage_caja')
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
    dinero_en_caja = payload.get('dinero_en_caja', '0')
    dinero_guardado = payload.get('dinero_guardado', '0')

    try:
        monto_declarado = Decimal(monto_declarado)
        if monto_declarado < 0:
            raise ValueError('El monto no puede ser negativo')
        
        # Convertir y validar distribución del dinero
        dinero_en_caja = Decimal(dinero_en_caja)
        dinero_guardado = Decimal(dinero_guardado)
        
        # Validar que al menos uno tenga valor
        if dinero_en_caja == 0 and dinero_guardado == 0:
            return JsonResponse({
                'success': False, 
                'error': 'Debes especificar cuánto dinero quedó en caja o cuánto se guardó'
            }, status=400)
        
        # Validar que la suma coincida con el monto declarado
        suma_distribucion = dinero_en_caja + dinero_guardado
        if abs(suma_distribucion - monto_declarado) > Decimal('0.01'):
            return JsonResponse({
                'success': False, 
                'error': f'La distribución (${suma_distribucion:,.0f}) no coincide con el total contado (${monto_declarado:,.0f})'
            }, status=400)

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
        
        # Guardar la distribución del dinero
        caja.dinero_en_caja = dinero_en_caja
        caja.dinero_guardado = dinero_guardado
        caja.save()

        return JsonResponse({
            'success': True,
            'message': 'Caja cerrada exitosamente',
            'diferencia': float(diferencia),
            'monto_final_declarado': float(caja.monto_final_declarado),
            'monto_final_sistema': float(caja.monto_final_sistema),
            'dinero_en_caja': float(caja.dinero_en_caja),
            'dinero_guardado': float(caja.dinero_guardado),
        })
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': f'Datos inválidos: {str(e)}'}, status=400)


@staff_or_permission_required('users.can_view_caja')
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


@staff_or_permission_required('users.can_manage_caja')
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


@staff_or_permission_required('users.can_view_caja')
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


@staff_or_permission_required('users.can_view_caja')
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


@staff_or_permission_required('users.can_view_caja')
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


# ============================================================
# VISTAS DE INFORMES Y ESTADÍSTICAS
# ============================================================

@staff_or_permission_required('users.can_view_caja')
def informes_caja(request):
    """
    Vista principal de informes de caja con estadísticas completas.
    Muestra balance general, historial de arqueos y flujo de efectivo.
    """
    context = {
        'titulo': 'Informes de Caja',
    }
    return render(request, 'caja/informes.html', context)


@staff_or_permission_required('users.can_view_caja')
def balance_general_ajax(request):
    """
    Devuelve el balance general con filtrado por fechas.
    Soporta: última semana, últimos 30 días, últimos 2 meses, últimos 3 meses,
    día actual, día anterior, y rango personalizado.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener parámetros de filtro
        filtro_tipo = request.GET.get('filtro', 'ultima_semana')
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        
        # Calcular rango de fechas según el tipo de filtro
        now = timezone.now()
        
        if filtro_tipo == 'dia_actual':
            fecha_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = now
        elif filtro_tipo == 'dia_anterior':
            ayer = now - timedelta(days=1)
            fecha_inicio = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filtro_tipo == 'ultima_semana':
            fecha_inicio = now - timedelta(days=7)
            fecha_fin = now
        elif filtro_tipo == 'ultimos_30_dias':
            fecha_inicio = now - timedelta(days=30)
            fecha_fin = now
        elif filtro_tipo == 'ultimos_2_meses':
            fecha_inicio = now - timedelta(days=60)
            fecha_fin = now
        elif filtro_tipo == 'ultimos_3_meses':
            fecha_inicio = now - timedelta(days=90)
            fecha_fin = now
        elif filtro_tipo == 'rango_personalizado':
            if not fecha_desde or not fecha_hasta:
                return JsonResponse({'error': 'Fechas requeridas para rango personalizado'}, status=400)
            fecha_inicio = timezone.make_aware(datetime.strptime(fecha_desde, '%Y-%m-%d'))
            fecha_fin = timezone.make_aware(datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        else:
            # Por defecto: última semana
            fecha_inicio = now - timedelta(days=7)
            fecha_fin = now
        
        # Obtener cajas cerradas en el rango de fechas
        cajas = CajaRegistradora.objects.filter(
            estado='CERRADA',
            fecha_cierre__gte=fecha_inicio,
            fecha_cierre__lte=fecha_fin
        )
        
        # Calcular totales
        total_dinero_guardado = cajas.aggregate(
            total=Sum('dinero_guardado')
        )['total'] or Decimal('0.00')
        
        # Total de ingresos y egresos del periodo
        movimientos = MovimientoCaja.objects.filter(
            caja__in=cajas,
            fecha_movimiento__gte=fecha_inicio,
            fecha_movimiento__lte=fecha_fin
        )
        
        total_ingresos = movimientos.filter(
            tipo='INGRESO'
        ).exclude(
            tipo_movimiento__codigo='APERTURA'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        total_egresos = movimientos.filter(
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        flujo_neto = total_ingresos - total_egresos
        
        # Estadísticas adicionales
        num_cajas = cajas.count()
        total_dinero_en_caja = cajas.aggregate(
            total=Sum('dinero_en_caja')
        )['total'] or Decimal('0.00')
        
        # Promedio de diferencias (descuadres)
        promedio_diferencia = cajas.aggregate(
            promedio=Avg('diferencia')
        )['promedio'] or Decimal('0.00')
        
        return JsonResponse({
            'success': True,
            'balance': {
                'total_dinero_guardado': float(total_dinero_guardado),
                'total_dinero_en_caja': float(total_dinero_en_caja),
                'total_ingresos': float(total_ingresos),
                'total_egresos': float(total_egresos),
                'flujo_neto': float(flujo_neto),
                'num_cajas': num_cajas,
                'promedio_diferencia': float(promedio_diferencia),
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al calcular balance: {str(e)}'}, status=500)


@staff_or_permission_required('users.can_view_caja')
def historial_arqueos_ajax(request):
    """
    Devuelve el historial de arqueos (cajas cerradas) con paginación.
    Muestra las últimas 5 cajas por defecto.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Parámetros de paginación
        pagina = int(request.GET.get('pagina', 1))
        por_pagina = int(request.GET.get('por_pagina', 5))
        
        # Filtros de fecha (si se envían)
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        
        # Query base: cajas cerradas
        cajas = CajaRegistradora.objects.filter(estado='CERRADA')
        
        # Aplicar filtros de fecha si existen
        if fecha_desde:
            fecha_inicio = timezone.make_aware(datetime.strptime(fecha_desde, '%Y-%m-%d'))
            cajas = cajas.filter(fecha_cierre__gte=fecha_inicio)
        
        if fecha_hasta:
            fecha_fin = timezone.make_aware(datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            cajas = cajas.filter(fecha_cierre__lte=fecha_fin)
        
        # Ordenar por fecha de cierre descendente
        cajas = cajas.select_related('cajero').order_by('-fecha_cierre')
        
        # Total de registros
        total = cajas.count()
        
        # Calcular paginación
        inicio = (pagina - 1) * por_pagina
        fin = inicio + por_pagina
        cajas_paginadas = cajas[inicio:fin]
        
        # Construir lista de cajas con sus datos
        lista_cajas = []
        for caja in cajas_paginadas:
            # Calcular movimientos de la caja
            movimientos = MovimientoCaja.objects.filter(caja=caja)
            total_entradas = movimientos.filter(
                tipo='INGRESO'
            ).exclude(
                tipo_movimiento__codigo='APERTURA'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            total_salidas = movimientos.filter(
                tipo='EGRESO'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            # Saldo teórico
            saldo_teorico = caja.monto_inicial + total_entradas - total_salidas
            
            # Obtener nombre del cajero
            cajero_nombre = str(caja.cajero.username)
            try:
                full_name = caja.cajero.get_full_name()
                if full_name and full_name.strip():
                    cajero_nombre = full_name
            except:
                pass
            
            lista_cajas.append({
                'id': caja.id,
                'cajero': cajero_nombre,
                'fecha_apertura': caja.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
                'fecha_cierre': caja.fecha_cierre.strftime('%d/%m/%Y %H:%M') if caja.fecha_cierre else '-',
                'saldo_inicial': float(caja.monto_inicial),
                'total_entradas': float(total_entradas),
                'total_salidas': float(total_salidas),
                'saldo_teorico': float(saldo_teorico),
                'saldo_real': float(caja.monto_final_declarado or 0),
                'diferencia': float(caja.diferencia or 0),
                'dinero_en_caja': float(caja.dinero_en_caja or 0),
                'dinero_guardado': float(caja.dinero_guardado or 0),
            })
        
        # Calcular total de páginas
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return JsonResponse({
            'success': True,
            'cajas': lista_cajas,
            'paginacion': {
                'pagina_actual': pagina,
                'por_pagina': por_pagina,
                'total_registros': total,
                'total_paginas': total_paginas,
                'tiene_anterior': pagina > 1,
                'tiene_siguiente': pagina < total_paginas,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al cargar historial: {str(e)}'}, status=500)


@staff_or_permission_required('users.can_view_caja')
def flujo_efectivo_ajax(request):
    """
    Devuelve el reporte de flujo de efectivo consolidado por periodo.
    Permite analizar ingresos, egresos y flujo neto en un rango de fechas.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener parámetros de filtro
        filtro_tipo = request.GET.get('filtro', 'ultima_semana')
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        
        # Calcular rango de fechas
        now = timezone.now()
        
        if filtro_tipo == 'dia_actual':
            fecha_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = now
        elif filtro_tipo == 'dia_anterior':
            ayer = now - timedelta(days=1)
            fecha_inicio = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filtro_tipo == 'ultima_semana':
            fecha_inicio = now - timedelta(days=7)
            fecha_fin = now
        elif filtro_tipo == 'ultimos_30_dias':
            fecha_inicio = now - timedelta(days=30)
            fecha_fin = now
        elif filtro_tipo == 'ultimos_2_meses':
            fecha_inicio = now - timedelta(days=60)
            fecha_fin = now
        elif filtro_tipo == 'ultimos_3_meses':
            fecha_inicio = now - timedelta(days=90)
            fecha_fin = now
        elif filtro_tipo == 'rango_personalizado':
            if not fecha_desde or not fecha_hasta:
                return JsonResponse({'error': 'Fechas requeridas para rango personalizado'}, status=400)
            fecha_inicio = timezone.make_aware(datetime.strptime(fecha_desde, '%Y-%m-%d'))
            fecha_fin = timezone.make_aware(datetime.strptime(fecha_hasta + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        else:
            fecha_inicio = now - timedelta(days=7)
            fecha_fin = now
        
        # Obtener todos los movimientos del periodo
        movimientos = MovimientoCaja.objects.filter(
            fecha_movimiento__gte=fecha_inicio,
            fecha_movimiento__lte=fecha_fin
        ).select_related('tipo_movimiento')
        
        # Calcular totales por tipo de movimiento
        ingresos_por_tipo = movimientos.filter(
            tipo='INGRESO'
        ).exclude(
            tipo_movimiento__codigo='APERTURA'
        ).values(
            'tipo_movimiento__nombre'
        ).annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        ).order_by('-total')
        
        egresos_por_tipo = movimientos.filter(
            tipo='EGRESO'
        ).values(
            'tipo_movimiento__nombre'
        ).annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        ).order_by('-total')
        
        # Totales generales
        total_ingresos = sum(item['total'] for item in ingresos_por_tipo)
        total_egresos = sum(item['total'] for item in egresos_por_tipo)
        flujo_neto = total_ingresos - total_egresos
        
        # Convertir a listas serializables
        ingresos_lista = [
            {
                'tipo': item['tipo_movimiento__nombre'],
                'total': float(item['total']),
                'cantidad': item['cantidad']
            }
            for item in ingresos_por_tipo
        ]
        
        egresos_lista = [
            {
                'tipo': item['tipo_movimiento__nombre'],
                'total': float(item['total']),
                'cantidad': item['cantidad']
            }
            for item in egresos_por_tipo
        ]
        
        return JsonResponse({
            'success': True,
            'flujo': {
                'total_ingresos': float(total_ingresos),
                'total_egresos': float(total_egresos),
                'flujo_neto': float(flujo_neto),
                'ingresos_por_tipo': ingresos_lista,
                'egresos_por_tipo': egresos_lista,
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al calcular flujo: {str(e)}'}, status=500)


@staff_or_permission_required('users.can_view_caja')
def detalle_caja_modal_ajax(request, caja_id):
    """
    Devuelve el detalle completo de una caja para mostrar en modal.
    Incluye: fechas, monto inicial con denominaciones, movimientos, cierre con denominaciones.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener la caja
        caja = get_object_or_404(CajaRegistradora, id=caja_id)
        
        # Información básica
        cajero_nombre = str(caja.cajero.username)
        try:
            full_name = caja.cajero.get_full_name()
            if full_name and full_name.strip():
                cajero_nombre = full_name
        except:
            pass
        
        # Conteo de apertura (denominaciones con las que se abrió)
        conteo_apertura = None
        conteo_apertura_obj = ConteoEfectivo.objects.filter(
            caja=caja, 
            tipo_conteo='APERTURA'
        ).first()
        
        if conteo_apertura_obj:
            detalles_apertura = DetalleConteo.objects.filter(
                conteo=conteo_apertura_obj
            ).select_related('denominacion').order_by('-denominacion__valor')
            
            conteo_apertura = {
                'total': float(conteo_apertura_obj.total),
                'detalles': [
                    {
                        'denominacion': str(detalle.denominacion),
                        'valor': float(detalle.denominacion.valor),
                        'tipo': detalle.denominacion.tipo,
                        'cantidad': detalle.cantidad,
                        'subtotal': float(detalle.subtotal)
                    }
                    for detalle in detalles_apertura
                ]
            }
        
        # Conteo de cierre (denominaciones con las que se cerró)
        conteo_cierre = None
        conteo_cierre_obj = ConteoEfectivo.objects.filter(
            caja=caja, 
            tipo_conteo='CIERRE'
        ).first()
        
        if conteo_cierre_obj:
            detalles_cierre = DetalleConteo.objects.filter(
                conteo=conteo_cierre_obj
            ).select_related('denominacion').order_by('-denominacion__valor')
            
            conteo_cierre = {
                'total': float(conteo_cierre_obj.total),
                'detalles': [
                    {
                        'denominacion': str(detalle.denominacion),
                        'valor': float(detalle.denominacion.valor),
                        'tipo': detalle.denominacion.tipo,
                        'cantidad': detalle.cantidad,
                        'subtotal': float(detalle.subtotal)
                    }
                    for detalle in detalles_cierre
                ]
            }
        
        # Movimientos de la caja
        movimientos = MovimientoCaja.objects.filter(
            caja=caja
        ).select_related('tipo_movimiento', 'usuario').order_by('fecha_movimiento')
        
        movimientos_lista = []
        total_ingresos = Decimal('0.00')
        total_egresos = Decimal('0.00')
        
        for mov in movimientos:
            usuario_mov = str(mov.usuario.username)
            try:
                full_name_mov = mov.usuario.get_full_name()
                if full_name_mov and full_name_mov.strip():
                    usuario_mov = full_name_mov
            except:
                pass
            
            if mov.tipo == 'INGRESO':
                total_ingresos += mov.monto
            else:
                total_egresos += mov.monto
            
            movimientos_lista.append({
                'id': mov.id,
                'fecha': mov.fecha_movimiento.strftime('%d/%m/%Y %H:%M:%S'),
                'tipo': mov.tipo,
                'tipo_movimiento': mov.tipo_movimiento.nombre,
                'monto': float(mov.monto),
                'descripcion': mov.descripcion or '-',
                'referencia': mov.referencia or '-',
                'usuario': usuario_mov,
            })
        
        # Saldo teórico
        saldo_teorico = caja.monto_inicial + total_ingresos - total_egresos
        
        return JsonResponse({
            'success': True,
            'caja': {
                'id': caja.id,
                'cajero': cajero_nombre,
                'estado': caja.estado,
                'fecha_apertura': caja.fecha_apertura.strftime('%d/%m/%Y %H:%M:%S'),
                'fecha_cierre': caja.fecha_cierre.strftime('%d/%m/%Y %H:%M:%S') if caja.fecha_cierre else None,
                'monto_inicial': float(caja.monto_inicial),
                'monto_final_declarado': float(caja.monto_final_declarado or 0),
                'monto_final_sistema': float(caja.monto_final_sistema or 0),
                'diferencia': float(caja.diferencia or 0),
                'dinero_en_caja': float(caja.dinero_en_caja or 0),
                'dinero_guardado': float(caja.dinero_guardado or 0),
                'observaciones_apertura': caja.observaciones_apertura or '-',
                'observaciones_cierre': caja.observaciones_cierre or '-',
                'saldo_teorico': float(saldo_teorico),
                'total_ingresos': float(total_ingresos),
                'total_egresos': float(total_egresos),
                'conteo_apertura': conteo_apertura,
                'conteo_cierre': conteo_cierre,
                'movimientos': movimientos_lista,
                'num_movimientos': len(movimientos_lista),
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al cargar detalle: {str(e)}'}, status=500)
