"""
Vistas del Dashboard Personalizado
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from caja.models import CajaRegistradora, MovimientoCaja
from facturacion.models import Factura

User = get_user_model()


@login_required
def dashboard_home(request):
    """
    Vista principal del dashboard con resumen general
    """
    # Estadísticas generales
    total_usuarios = User.objects.count()
    
    # Caja actual
    caja_actual = CajaRegistradora.objects.filter(estado='ABIERTA').first()
    caja_dinero = caja_actual.dinero_en_caja if caja_actual else Decimal('0.00')
    
    # Movimientos de hoy
    hoy = timezone.now().date()
    movimientos_hoy = MovimientoCaja.objects.filter(
        fecha_movimiento__date=hoy
    ).count()
    
    # Facturas del mes
    inicio_mes = timezone.now().replace(day=1)
    facturas_mes = Factura.objects.filter(
        fecha_emision__gte=inicio_mes
    ).count()
    
    context = {
        'total_usuarios': total_usuarios,
        'caja_dinero': caja_dinero,
        'caja_abierta': caja_actual is not None,
        'movimientos_hoy': movimientos_hoy,
        'facturas_mes': facturas_mes,
    }
    
    return render(request, 'dashboard_custom/home.html', context)


@login_required
def usuarios_list(request):
    """
    Lista de todos los usuarios del sistema
    """
    # Obtener parámetros de búsqueda y filtro
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Consulta base
    usuarios = User.objects.all().order_by('-date_joined')
    
    # Aplicar búsqueda
    if search:
        usuarios = usuarios.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Aplicar filtro de estado
    if status_filter == 'active':
        usuarios = usuarios.filter(is_active=True)
    elif status_filter == 'inactive':
        usuarios = usuarios.filter(is_active=False)
    elif status_filter == 'staff':
        usuarios = usuarios.filter(is_staff=True)
    
    context = {
        'usuarios': usuarios,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard_custom/usuarios.html', context)


@login_required
def estadisticas_caja(request):
    """
    Vista de estadísticas de caja con gráficos y métricas
    """
    # Obtener rango de fechas (últimos 30 días por defecto)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Permitir filtro personalizado
    if request.GET.get('fecha_inicio'):
        try:
            fecha_inicio = timezone.datetime.strptime(
                request.GET.get('fecha_inicio'), '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    if request.GET.get('fecha_fin'):
        try:
            fecha_fin = timezone.datetime.strptime(
                request.GET.get('fecha_fin'), '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    # Obtener movimientos del período
    movimientos = MovimientoCaja.objects.filter(
        fecha_movimiento__date__gte=fecha_inicio,
        fecha_movimiento__date__lte=fecha_fin
    )
    
    # Calcular totales
    total_ingresos = movimientos.filter(tipo='INGRESO').aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    # Movimientos por día (para gráfico)
    movimientos_por_dia = {}
    current_date = fecha_inicio
    while current_date <= fecha_fin:
        ingresos_dia = movimientos.filter(
            fecha_movimiento__date=current_date,
            tipo='INGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        egresos_dia = movimientos.filter(
            fecha_movimiento__date=current_date,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        movimientos_por_dia[current_date.strftime('%Y-%m-%d')] = {
            'ingresos': float(ingresos_dia),
            'egresos': float(egresos_dia),
        }
        
        current_date += timedelta(days=1)
    
    # Últimos movimientos
    ultimos_movimientos = movimientos.order_by('-fecha_movimiento')[:10]
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': total_ingresos - total_egresos,
        'total_movimientos': movimientos.count(),
        'movimientos_por_dia': movimientos_por_dia,
        'ultimos_movimientos': ultimos_movimientos,
    }
    
    return render(request, 'dashboard_custom/estadisticas.html', context)
