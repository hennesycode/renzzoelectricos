"""
Vistas para el módulo de Tesorería.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    Cuenta, TransaccionGeneral
)
from .decorators import staff_or_permission_required


@staff_or_permission_required('users.can_view_caja')
def tesoreria_dashboard(request):
    """
    Dashboard principal de Tesorería.
    Muestra saldos de Caja, Banco y Dinero Guardado.
    """
    # Obtener cuenta banco y reserva
    cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
    cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
    
    # Obtener caja abierta
    caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
    
    # ========== CALCULAR DINERO EN CAJA ==========
    saldo_caja = Decimal('0.00')
    
    if caja_abierta:
        # Caja ABIERTA: calcular en tiempo real (SIN entradas banco)
        movimientos = MovimientoCaja.objects.filter(caja=caja_abierta)
        
        # Total de ingresos EN EFECTIVO (excluir apertura y banco)
        total_ingresos = movimientos.filter(
            tipo='INGRESO'
        ).exclude(
            tipo_movimiento__codigo='APERTURA'
        ).exclude(
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Dinero en caja = monto inicial + ingresos efectivo - egresos
        saldo_caja = caja_abierta.monto_inicial + total_ingresos - total_egresos
    else:
        # Caja CERRADA: mostrar dinero_en_caja de la última caja cerrada
        ultima_caja_cerrada = CajaRegistradora.objects.filter(
            estado='CERRADA'
        ).order_by('-fecha_cierre').first()
        
        if ultima_caja_cerrada and ultima_caja_cerrada.dinero_en_caja:
            saldo_caja = ultima_caja_cerrada.dinero_en_caja
    
    # ========== CALCULAR BANCO PRINCIPAL ==========
    # Suma de TODAS las entradas [BANCO] de MovimientoCaja
    total_entradas_banco = MovimientoCaja.objects.filter(
        tipo='INGRESO',
        descripcion__icontains='[BANCO]'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # MENOS: Egresos desde Banco (gastos y compras)
    egresos_banco = Decimal('0.00')
    ingresos_banco = Decimal('0.00')
    
    if cuenta_banco:
        # Egresos desde banco
        egresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Ingresos a banco (transferencias hacia banco)
        ingresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='INGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # Banco = Entradas banco + Ingresos - Egresos
    saldo_banco = total_entradas_banco + ingresos_banco - egresos_banco
    
    # ========== CALCULAR DINERO GUARDADO ==========
    # Suma de TODO el dinero guardado de TODAS las cajas cerradas
    total_guardado_cajas = CajaRegistradora.objects.filter(
        estado='CERRADA',
        dinero_guardado__gt=0
    ).aggregate(total=Sum('dinero_guardado'))['total'] or Decimal('0.00')
    
    # MENOS: Egresos desde Dinero Guardado
    egresos_reserva = Decimal('0.00')
    ingresos_reserva = Decimal('0.00')
    
    if cuenta_reserva:
        # Egresos desde reserva (gastos y compras)
        egresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Ingresos a reserva (transferencias hacia reserva)
        ingresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='INGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # CALCULAR: Dinero Guardado = Total de cajas + Ingresos - Egresos
    saldo_reserva = total_guardado_cajas + ingresos_reserva - egresos_reserva
    
    # ========== TOTAL DISPONIBLE ==========
    saldo_total = saldo_caja + saldo_banco + saldo_reserva
    
    # Obtener últimas transacciones de Tesorería
    transacciones = TransaccionGeneral.objects.select_related(
        'tipo_movimiento', 'cuenta', 'usuario'
    ).order_by('-fecha')[:20]
    
    context = {
        'saldo_caja': saldo_caja,
        'saldo_banco': saldo_banco,
        'saldo_reserva': saldo_reserva,
        'saldo_total': saldo_total,
        'transacciones': transacciones,
        'cuenta_banco': cuenta_banco,
        'cuenta_reserva': cuenta_reserva,
    }
    
    return render(request, 'caja/tesoreria/dashboard.html', context)


@staff_or_permission_required('users.can_manage_caja')
def get_saldos_tesoreria(request):
    """
    Devuelve los saldos actuales de todas las cuentas (Caja, Banco, Reserva).
    Endpoint JSON para actualización en tiempo real.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # ========== DINERO EN CAJA ==========
    caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
    saldo_caja = Decimal('0.00')
    
    if caja_abierta:
        # Caja ABIERTA: calcular en tiempo real (SIN entradas banco)
        movimientos = MovimientoCaja.objects.filter(caja=caja_abierta)
        
        total_ingresos = movimientos.filter(
            tipo='INGRESO'
        ).exclude(
            tipo_movimiento__codigo='APERTURA'
        ).exclude(
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        saldo_caja = caja_abierta.monto_inicial + total_ingresos - total_egresos
    else:
        # Caja CERRADA: mostrar dinero_en_caja de la última caja cerrada
        ultima_caja_cerrada = CajaRegistradora.objects.filter(
            estado='CERRADA'
        ).order_by('-fecha_cierre').first()
        
        if ultima_caja_cerrada and ultima_caja_cerrada.dinero_en_caja:
            saldo_caja = ultima_caja_cerrada.dinero_en_caja
    
    # ========== BANCO PRINCIPAL ==========
    # Suma de TODAS las entradas [BANCO] de MovimientoCaja
    cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
    banco_id = cuenta_banco.id if cuenta_banco else None
    
    total_entradas_banco = MovimientoCaja.objects.filter(
        tipo='INGRESO',
        descripcion__icontains='[BANCO]'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    egresos_banco = Decimal('0.00')
    ingresos_banco = Decimal('0.00')
    
    if cuenta_banco:
        # Egresos desde banco (gastos/compras)
        egresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Ingresos a banco (transferencias hacia banco)
        ingresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='INGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # Banco = Entradas banco + Ingresos - Egresos
    saldo_banco = total_entradas_banco + ingresos_banco - egresos_banco
    
    # ========== DINERO GUARDADO (RESERVA) ==========
    # Suma de TODO el dinero guardado de TODAS las cajas cerradas
    total_guardado_cajas = CajaRegistradora.objects.filter(
        estado='CERRADA',
        dinero_guardado__gt=0
    ).aggregate(total=Sum('dinero_guardado'))['total'] or Decimal('0.00')
    
    # MENOS: Egresos desde Dinero Guardado
    cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
    egresos_reserva = Decimal('0.00')
    ingresos_reserva = Decimal('0.00')
    reserva_id = None
    
    if cuenta_reserva:
        reserva_id = cuenta_reserva.id
        
        # Egresos desde reserva (gastos y compras)
        egresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Ingresos a reserva (transferencias hacia reserva)
        ingresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='INGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # Dinero Guardado = Total guardado de cajas + Ingresos - Egresos
    saldo_reserva = total_guardado_cajas + ingresos_reserva - egresos_reserva
    
    return JsonResponse({
        'success': True,
        'caja': {
            'saldo': float(saldo_caja)
        },
        'banco': {
            'id': banco_id,
            'saldo': float(saldo_banco)
        },
        'reserva': {
            'id': reserva_id,
            'saldo': float(saldo_reserva)
        }
    })


@staff_or_permission_required('users.can_manage_caja')
def get_tipos_movimiento_tesoreria(request):
    """
    Devuelve los tipos de movimiento filtrados por tipo_base.
    Para botón "Gasto" devuelve GASTO, para "Compra" devuelve INVERSION.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    filtro = request.GET.get('filtro', 'GASTO')  # GASTO o INVERSION
    
    tipos = TipoMovimiento.objects.filter(
        activo=True,
        tipo_base=filtro
    ).values('id', 'codigo', 'nombre')
    
    return JsonResponse({
        'success': True,
        'tipos': list(tipos)
    })


@staff_or_permission_required('users.can_manage_caja')
def registrar_egreso_tesoreria(request):
    """
    Registra un egreso (Gasto o Compra) desde Tesorería.
    Valida el origen del dinero y actualiza los saldos correspondientes.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        monto = Decimal(str(data.get('monto')))
        tipo_movimiento_id = data.get('tipo_movimiento_id')
        origen = data.get('origen')  # "CAJA", ID de Cuenta Banco, ID de Cuenta Reserva
        descripcion = data.get('descripcion', '')
        referencia = data.get('referencia', '')
        
        # Validaciones básicas
        if monto <= 0:
            return JsonResponse({'error': 'El monto debe ser mayor a cero'}, status=400)
        
        if not tipo_movimiento_id:
            return JsonResponse({'error': 'Debe seleccionar un tipo de movimiento'}, status=400)
        
        tipo_movimiento = TipoMovimiento.objects.get(id=tipo_movimiento_id)
        
        with transaction.atomic():
            if origen == 'CAJA':
                # Registrar egreso en Caja
                caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
                
                if not caja_abierta:
                    return JsonResponse({
                        'error': 'No hay una caja abierta. Debe abrir una caja primero.'
                    }, status=400)
                
                # Calcular saldo disponible
                movimientos = MovimientoCaja.objects.filter(caja=caja_abierta)
                
                total_entradas_banco = movimientos.filter(
                    tipo='INGRESO',
                    descripcion__icontains='[BANCO]'
                ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                
                total_ingresos = movimientos.filter(
                    tipo='INGRESO'
                ).exclude(
                    tipo_movimiento__codigo='APERTURA'
                ).exclude(
                    descripcion__icontains='[BANCO]'
                ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                
                total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
                    total=Sum('monto')
                )['total'] or Decimal('0.00')
                
                saldo_disponible = caja_abierta.monto_inicial + total_ingresos + total_entradas_banco - total_egresos
                
                if monto > saldo_disponible:
                    return JsonResponse({
                        'error': f'Fondos insuficientes en caja. Disponible: ${saldo_disponible:,.2f}'
                    }, status=400)
                
                # Crear MovimientoCaja
                MovimientoCaja.objects.create(
                    caja=caja_abierta,
                    tipo_movimiento=tipo_movimiento,
                    tipo='EGRESO',
                    monto=monto,
                    descripcion=descripcion,
                    referencia=referencia,
                    usuario=request.user
                )
                
                origen_nombre = "Caja"
                
            else:
                # Registrar egreso en Banco o Reserva
                try:
                    cuenta = Cuenta.objects.get(id=origen, activo=True)
                except Cuenta.DoesNotExist:
                    return JsonResponse({'error': 'La cuenta seleccionada no existe'}, status=400)
                
                # Validar fondos disponibles según cálculo dinámico
                if cuenta.tipo == 'BANCO':
                    # Calcular saldo banco dinámico
                    total_entradas = MovimientoCaja.objects.filter(
                        tipo='INGRESO',
                        descripcion__icontains='[BANCO]'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    egresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta,
                        tipo='EGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    ingresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta,
                        tipo='INGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    saldo_disponible = total_entradas + ingresos - egresos
                    
                    if monto > saldo_disponible:
                        return JsonResponse({
                            'error': f'Fondos insuficientes en {cuenta.nombre}. Disponible: ${saldo_disponible:,.2f}'
                        }, status=400)
                
                elif cuenta.tipo == 'RESERVA':
                    # Calcular saldo reserva dinámico
                    total_guardado = CajaRegistradora.objects.filter(
                        estado='CERRADA',
                        dinero_guardado__gt=0
                    ).aggregate(total=Sum('dinero_guardado'))['total'] or Decimal('0.00')
                    
                    egresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta,
                        tipo='EGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    ingresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta,
                        tipo='INGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    saldo_disponible = total_guardado + ingresos - egresos
                    
                    if monto > saldo_disponible:
                        return JsonResponse({
                            'error': f'Fondos insuficientes en {cuenta.nombre}. Disponible: ${saldo_disponible:,.2f}'
                        }, status=400)
                
                # Crear TransaccionGeneral
                TransaccionGeneral.objects.create(
                    tipo='EGRESO',
                    monto=monto,
                    descripcion=descripcion,
                    referencia=referencia,
                    tipo_movimiento=tipo_movimiento,
                    cuenta=cuenta,
                    usuario=request.user
                )
                
                # NO actualizamos saldo_actual porque ahora se calcula dinámicamente
                
                origen_nombre = cuenta.nombre
        
        return JsonResponse({
            'success': True,
            'message': f'Egreso registrado exitosamente desde {origen_nombre}',
            'origen': origen
        })
        
    except TipoMovimiento.DoesNotExist:
        return JsonResponse({'error': 'Tipo de movimiento no válido'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al registrar egreso: {str(e)}'}, status=500)


@staff_or_permission_required('users.can_manage_caja')
def transferir_fondos(request):
    """
    Transfiere fondos entre cuentas (Caja → Banco, Caja → Reserva, etc.).
    Se usa al cerrar caja o para movimientos internos.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        monto = Decimal(str(data.get('monto')))
        origen = data.get('origen')  # "CAJA" o ID de cuenta
        destino_id = data.get('destino_id')  # "CAJA" o ID de cuenta destino
        descripcion = data.get('descripcion', '')
        
        if monto <= 0:
            return JsonResponse({'error': 'El monto debe ser mayor a cero'}, status=400)
        
        # No permitir transferencias a CAJA (solo desde CAJA)
        if destino_id == 'CAJA':
            return JsonResponse({'error': 'No se puede transferir hacia la caja desde tesorería. Use el módulo de Caja.'}, status=400)
        
        with transaction.atomic():
            # Obtener cuenta destino
            try:
                cuenta_destino = Cuenta.objects.get(id=destino_id, activo=True)
            except (Cuenta.DoesNotExist, ValueError, TypeError):
                return JsonResponse({'error': 'Cuenta destino no válida'}, status=400)
            
            if origen == 'CAJA':
                # Transferir desde Caja
                caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
                
                if not caja_abierta:
                    return JsonResponse({'error': 'No hay una caja abierta'}, status=400)
                
                # Validar fondos (el monto a transferir debe ser <= saldo disponible)
                # Este flujo se ejecuta típicamente después de cerrar caja,
                # así que no validamos aquí (se asume que el frontend envía el monto correcto)
                
                # Crear TransaccionGeneral de ingreso a la cuenta destino
                tipo_mov_interno = TipoMovimiento.objects.filter(
                    codigo='APERTURA'
                ).first()  # Usamos APERTURA como tipo interno
                
                TransaccionGeneral.objects.create(
                    tipo='INGRESO',
                    monto=monto,
                    descripcion=f'Transferencia desde Caja. {descripcion}',
                    tipo_movimiento=tipo_mov_interno,
                    cuenta=cuenta_destino,
                    usuario=request.user
                )
                
                # NO actualizamos saldo_actual porque ahora se calcula dinámicamente
                
                origen_nombre = "Caja"
                
            else:
                # Transferir entre cuentas
                try:
                    cuenta_origen = Cuenta.objects.get(id=origen, activo=True)
                except Cuenta.DoesNotExist:
                    return JsonResponse({'error': 'Cuenta origen no válida'}, status=400)
                
                # Validar fondos disponibles según cálculo dinámico
                if cuenta_origen.tipo == 'BANCO':
                    total_entradas = MovimientoCaja.objects.filter(
                        tipo='INGRESO',
                        descripcion__icontains='[BANCO]'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    egresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta_origen,
                        tipo='EGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    ingresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta_origen,
                        tipo='INGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    saldo_disponible = total_entradas + ingresos - egresos
                    
                elif cuenta_origen.tipo == 'RESERVA':
                    total_guardado = CajaRegistradora.objects.filter(
                        estado='CERRADA',
                        dinero_guardado__gt=0
                    ).aggregate(total=Sum('dinero_guardado'))['total'] or Decimal('0.00')
                    
                    egresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta_origen,
                        tipo='EGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    ingresos = TransaccionGeneral.objects.filter(
                        cuenta=cuenta_origen,
                        tipo='INGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    saldo_disponible = total_guardado + ingresos - egresos
                else:
                    saldo_disponible = cuenta_origen.saldo_actual
                
                if monto > saldo_disponible:
                    return JsonResponse({
                        'error': f'Fondos insuficientes en {cuenta_origen.nombre}. Disponible: ${saldo_disponible:,.2f}'
                    }, status=400)
                
                # Registrar EGRESO de cuenta origen
                tipo_mov_interno = TipoMovimiento.objects.filter(codigo='APERTURA').first()
                
                TransaccionGeneral.objects.create(
                    tipo='EGRESO',
                    monto=monto,
                    descripcion=f'Transferencia hacia {cuenta_destino.nombre}. {descripcion}',
                    tipo_movimiento=tipo_mov_interno,
                    cuenta=cuenta_origen,
                    usuario=request.user
                )
                
                # Registrar INGRESO a cuenta destino
                TransaccionGeneral.objects.create(
                    tipo='INGRESO',
                    monto=monto,
                    descripcion=f'Transferencia desde {cuenta_origen.nombre}. {descripcion}',
                    tipo_movimiento=tipo_mov_interno,
                    cuenta=cuenta_destino,
                    usuario=request.user
                )
                
                # NO actualizamos saldo_actual porque ahora se calcula dinámicamente
                
                origen_nombre = cuenta_origen.nombre
        
        return JsonResponse({
            'success': True,
            'message': f'Transferencia exitosa de {origen_nombre} a {cuenta_destino.nombre}',
            'origen': origen,
            'destino': destino_id
        })
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al transferir fondos: {str(e)}'}, status=500)
