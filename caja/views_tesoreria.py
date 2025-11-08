"""
Vistas para el módulo de Tesorería.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
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
        
        # Total de ingresos EN EFECTIVO (incluir apertura, excluir banco)
        total_ingresos = movimientos.filter(
            tipo='INGRESO'
        ).exclude(
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Dinero en caja = total ingresos efectivo - total egresos
        # (total_ingresos ya incluye la apertura)
        saldo_caja = total_ingresos - total_egresos
    else:
        # Caja CERRADA: mostrar dinero_en_caja de la última caja cerrada
        ultima_caja_cerrada = CajaRegistradora.objects.filter(
            estado='CERRADA'
        ).order_by('-fecha_cierre').first()
        
        if ultima_caja_cerrada and ultima_caja_cerrada.dinero_en_caja:
            saldo_caja = ultima_caja_cerrada.dinero_en_caja
    
    # ========== CALCULAR BANCO PRINCIPAL ==========
    # Calcular saldo dinámicamente: entradas banco - gastos/compras desde banco
    
    # 1. Suma de TODAS las entradas [BANCO] de MovimientoCaja
    total_entradas_banco = MovimientoCaja.objects.filter(
        tipo='INGRESO',
        descripcion__icontains='[BANCO]'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # 2. Restar gastos/compras realizados desde banco (TransaccionGeneral de tipo EGRESO en cuenta banco)
    total_egresos_banco = Decimal('0.00')
    if cuenta_banco:
        total_egresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # 3. Saldo banco = entradas - egresos
    saldo_banco = total_entradas_banco - total_egresos_banco
    
    # ========== CALCULAR DINERO GUARDADO ==========
    # El dinero guardado se calcula SOLO de las cajas cerradas
    # Las transacciones automáticas de cierre se crean pero NO se suman (evitar duplicación)
    cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
    
    # Total de dinero guardado de cierres de caja
    cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
    total_dinero_guardado_cajas = sum(
        caja.dinero_guardado or Decimal('0.00') 
        for caja in cajas_cerradas
    )
    
    # Solo transacciones manuales en cuenta reserva (NO incluir cierres automáticos)
    transacciones_reserva_manuales = Decimal('0.00')
    if cuenta_reserva:
        # Excluir transacciones automáticas de cierre para evitar duplicación
        ingresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='INGRESO'
        ).exclude(
            descripcion__icontains='Cierre caja'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        egresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='EGRESO'
        ).exclude(
            descripcion__icontains='Cierre caja'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        transacciones_reserva_manuales = ingresos_reserva - egresos_reserva
    
    # SOLO el dinero de cajas + ajustes manuales (NO duplicar cierres automáticos)
    saldo_reserva = total_dinero_guardado_cajas + transacciones_reserva_manuales
    
    # ========== TOTAL DISPONIBLE ==========
    saldo_total = saldo_caja + saldo_banco + saldo_reserva
    
    # Obtener TODAS las transacciones de Tesorería
    transacciones = TransaccionGeneral.objects.select_related(
        'tipo_movimiento', 'cuenta', 'usuario'
    ).order_by('-fecha')
    
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
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        saldo_caja = total_ingresos - total_egresos
    else:
        # Caja CERRADA: mostrar dinero_en_caja de la última caja cerrada
        ultima_caja_cerrada = CajaRegistradora.objects.filter(
            estado='CERRADA'
        ).order_by('-fecha_cierre').first()
        
        if ultima_caja_cerrada and ultima_caja_cerrada.dinero_en_caja:
            saldo_caja = ultima_caja_cerrada.dinero_en_caja
    
    # ========== BANCO PRINCIPAL ==========
    # Calcular saldo dinámicamente: entradas banco - gastos/compras desde banco
    cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
    banco_id = cuenta_banco.id if cuenta_banco else None
    
    # 1. Suma de TODAS las entradas [BANCO] de MovimientoCaja
    total_entradas_banco = MovimientoCaja.objects.filter(
        tipo='INGRESO',
        descripcion__icontains='[BANCO]'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # 2. Restar gastos/compras realizados desde banco
    total_egresos_banco = Decimal('0.00')
    if cuenta_banco:
        total_egresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    # 3. Saldo banco = entradas - egresos
    saldo_banco = total_entradas_banco - total_egresos_banco
    
    # ========== DINERO GUARDADO (RESERVA) ==========
    # El dinero guardado se calcula SOLO de las cajas cerradas
    # Las transacciones automáticas de cierre se crean pero NO se suman (evitar duplicación)
    cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
    reserva_id = cuenta_reserva.id if cuenta_reserva else None
    
    # Total de dinero guardado de cierres de caja
    cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
    total_dinero_guardado_cajas = sum(
        caja.dinero_guardado or Decimal('0.00') 
        for caja in cajas_cerradas
    )
    
    # Solo transacciones manuales en cuenta reserva (NO incluir cierres automáticos)
    transacciones_reserva_manuales = Decimal('0.00')
    if cuenta_reserva:
        # Excluir transacciones automáticas de cierre para evitar duplicación
        ingresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='INGRESO'
        ).exclude(
            descripcion__icontains='Cierre caja'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        egresos_reserva = TransaccionGeneral.objects.filter(
            cuenta=cuenta_reserva,
            tipo='EGRESO'
        ).exclude(
            descripcion__icontains='Cierre caja'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        transacciones_reserva_manuales = ingresos_reserva - egresos_reserva
    
    # SOLO el dinero de cajas + ajustes manuales (NO duplicar cierres automáticos)
    saldo_reserva = total_dinero_guardado_cajas + transacciones_reserva_manuales
    
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
                    descripcion__icontains='[BANCO]'
                ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                
                total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
                    total=Sum('monto')
                )['total'] or Decimal('0.00')
                
                # Saldo disponible = dinero en caja + entradas banco
                # dinero_en_caja = total_ingresos - total_egresos (ya incluye apertura)
                dinero_en_caja = total_ingresos - total_egresos
                saldo_disponible = dinero_en_caja + total_entradas_banco
                
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
                
                # Validar fondos disponibles calculando dinámicamente
                if cuenta.tipo == 'BANCO':
                    # Calcular saldo banco dinámicamente: entradas - egresos
                    entradas_banco = MovimientoCaja.objects.filter(
                        tipo='INGRESO',
                        descripcion__icontains='[BANCO]'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    egresos_banco = TransaccionGeneral.objects.filter(
                        cuenta=cuenta,
                        tipo='EGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    saldo_disponible = entradas_banco - egresos_banco
                    
                    if monto > saldo_disponible:
                        return JsonResponse({
                            'error': f'Fondos insuficientes en {cuenta.nombre}. Disponible: ${saldo_disponible:,.2f}'
                        }, status=400)
                
                elif cuenta.tipo == 'RESERVA':
                    # Para RESERVA, usar dinero_guardado de las cajas cerradas
                    cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
                    total_cajas_cerradas = sum(
                        caja.dinero_guardado or Decimal('0.00') 
                        for caja in cajas_cerradas
                    )
                    
                    # Sumar/restar transacciones directas en la cuenta RESERVA
                    transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta)
                    ingresos = transacciones.filter(tipo='INGRESO').aggregate(
                        total=Sum('monto')
                    )['total'] or Decimal('0.00')
                    egresos = transacciones.filter(tipo='EGRESO').aggregate(
                        total=Sum('monto')
                    )['total'] or Decimal('0.00')
                    
                    saldo_disponible = total_cajas_cerradas + ingresos - egresos
                    
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
                tipo_mov_interno, _ = TipoMovimiento.objects.get_or_create(
                    codigo='TRANSFERENCIA',
                    defaults={
                        'nombre': 'Transferencia entre Cuentas',
                        'descripcion': 'Movimiento de fondos entre cuentas',
                        'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
                        'activo': True
                    }
                )
                
                TransaccionGeneral.objects.create(
                    tipo='INGRESO',
                    monto=monto,
                    descripcion=f'Transferencia desde Caja. {descripcion}',
                    referencia=f'TRANSFER-CAJA-{timezone.now().strftime("%Y%m%d-%H%M%S")}',
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
                
                # Validar fondos disponibles calculando dinámicamente
                if cuenta_origen.tipo == 'BANCO':
                    # Calcular saldo banco dinámicamente: entradas - egresos
                    entradas_banco = MovimientoCaja.objects.filter(
                        tipo='INGRESO',
                        descripcion__icontains='[BANCO]'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    egresos_banco = TransaccionGeneral.objects.filter(
                        cuenta=cuenta_origen,
                        tipo='EGRESO'
                    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
                    
                    saldo_disponible = entradas_banco - egresos_banco
                    
                elif cuenta_origen.tipo == 'RESERVA':
                    # Usar dinero_guardado de las cajas cerradas
                    cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
                    total_cajas_cerradas = sum(
                        caja.dinero_guardado or Decimal('0.00') 
                        for caja in cajas_cerradas
                    )
                    
                    # Sumar/restar transacciones directas en la cuenta RESERVA
                    transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta_origen)
                    ingresos = transacciones.filter(tipo='INGRESO').aggregate(
                        total=Sum('monto')
                    )['total'] or Decimal('0.00')
                    egresos = transacciones.filter(tipo='EGRESO').aggregate(
                        total=Sum('monto')
                    )['total'] or Decimal('0.00')
                    
                    saldo_disponible = total_cajas_cerradas + ingresos - egresos
                else:
                    saldo_disponible = cuenta_origen.saldo_actual
                
                if monto > saldo_disponible:
                    return JsonResponse({
                        'error': f'Fondos insuficientes en {cuenta_origen.nombre}. Disponible: ${saldo_disponible:,.2f}'
                    }, status=400)
                
                # Obtener tipo de movimiento para transferencias
                tipo_mov_interno, _ = TipoMovimiento.objects.get_or_create(
                    codigo='TRANSFERENCIA',
                    defaults={
                        'nombre': 'Transferencia entre Cuentas',
                        'descripcion': 'Movimiento de fondos entre cuentas',
                        'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
                        'activo': True
                    }
                )
                
                referencia_transferencia = f'TRANSFER-{timezone.now().strftime("%Y%m%d-%H%M%S")}'
                
                # Registrar EGRESO de cuenta origen
                TransaccionGeneral.objects.create(
                    tipo='EGRESO',
                    monto=monto,
                    descripcion=f'Transferencia hacia {cuenta_destino.nombre}. {descripcion}',
                    referencia=referencia_transferencia,
                    tipo_movimiento=tipo_mov_interno,
                    cuenta=cuenta_origen,
                    usuario=request.user
                )
                
                # Registrar INGRESO a cuenta destino
                TransaccionGeneral.objects.create(
                    tipo='INGRESO',
                    monto=monto,
                    descripcion=f'Transferencia desde {cuenta_origen.nombre}. {descripcion}',
                    referencia=referencia_transferencia,
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


@login_required
@require_http_methods(["POST"])
def aplicar_balance_cuentas(request):
    """
    Aplica balance/ajuste de cuentas creando transacciones para corregir diferencias.
    Crea una transacción individual por cada cuenta que tenga diferencias.
    """
    try:
        data = json.loads(request.body)
        cambios = data.get('cambios', [])
        
        if not cambios:
            return JsonResponse({'error': 'No hay cambios para aplicar'}, status=400)
        
        transacciones_creadas = 0
        resumen_cambios = []
        
        # Obtener cuentas necesarias
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        
        # Obtener tipo de movimiento para balance
        tipo_balance, created = TipoMovimiento.objects.get_or_create(
            codigo='BALANCE',
            defaults={
                'nombre': 'Balance de Cuentas',
                'descripcion': 'Ajuste por diferencias de balance',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
                'activo': True
            }
        )
        
        with transaction.atomic():
            for cambio in cambios:
                cuenta_tipo = cambio['cuenta']  # solo 'banco', 'reserva' (caja no aplica para balance)
                saldo_sistema = Decimal(str(cambio['saldo_sistema']))
                saldo_real = Decimal(str(cambio['saldo_real']))
                diferencia = Decimal(str(cambio['diferencia']))
                
                if diferencia == 0:
                    continue  # Sin diferencia, saltar
                
                # Determinar tipo de transacción y descripción
                if diferencia > 0:
                    tipo_transaccion = TransaccionGeneral.TipoTransaccionChoices.INGRESO
                    descripcion = f"Balance: Ajuste positivo en "
                else:
                    tipo_transaccion = TransaccionGeneral.TipoTransaccionChoices.EGRESO
                    descripcion = f"Balance: Ajuste negativo en "
                
                # Procesar según el tipo de cuenta (solo banco y reserva)
                if cuenta_tipo == 'banco' and cuenta_banco:
                    descripcion += f"Banco Principal (${saldo_sistema:,.0f} → ${saldo_real:,.0f})"
                    
                    # Crear transacción en banco
                    TransaccionGeneral.objects.create(
                        fecha=timezone.now(),
                        tipo=tipo_transaccion,
                        monto=abs(diferencia),
                        descripcion=descripcion,
                        referencia=f"Balance-{timezone.now().strftime('%Y%m%d-%H%M%S')}",
                        tipo_movimiento=tipo_balance,
                        cuenta=cuenta_banco,
                        usuario=request.user
                    )
                    
                    # Actualizar saldo de la cuenta banco
                    cuenta_banco.saldo_actual = saldo_real
                    cuenta_banco.save()
                    
                    transacciones_creadas += 1
                    resumen_cambios.append(f"Banco Principal: ${diferencia:+,.0f}")
                    
                elif cuenta_tipo == 'reserva' and cuenta_reserva:
                    descripcion += f"Dinero Guardado (${saldo_sistema:,.0f} → ${saldo_real:,.0f})"
                    
                    # Para dinero guardado, crear transacción de ajuste en cuenta RESERVA
                    # Esto representa ajustes manuales al dinero guardado físico
                    TransaccionGeneral.objects.create(
                        fecha=timezone.now(),
                        tipo=tipo_transaccion,
                        monto=abs(diferencia),
                        descripcion=descripcion,
                        referencia=f"Balance-{timezone.now().strftime('%Y%m%d-%H%M%S')}",
                        tipo_movimiento=tipo_balance,
                        cuenta=cuenta_reserva,
                        usuario=request.user
                    )
                    
                    # NO actualizamos saldo_actual de RESERVA porque se calcula dinámicamente
                    # La transacción creada arriba ya representa el ajuste necesario
                    
                    transacciones_creadas += 1
                    resumen_cambios.append(f"Dinero Guardado: ${diferencia:+,.0f}")
        
        # Mensaje de respuesta
        mensaje = f"Balance aplicado exitosamente. {', '.join(resumen_cambios)}."
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'transacciones_creadas': transacciones_creadas,
            'cambios_aplicados': resumen_cambios
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al aplicar balance: {str(e)}'}, status=500)
