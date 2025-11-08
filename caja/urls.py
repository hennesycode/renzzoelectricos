"""
URLs para el sistema de caja registradora.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.urls import path
from . import views
from . import views_tesoreria

app_name = 'caja'

urlpatterns = [
    # Dashboard principal de caja
    path('', views.caja_dashboard, name='dashboard'),
    
    # Gestión de caja
    path('abrir/', views.abrir_caja, name='abrir'),
    path('cerrar/', views.cerrar_caja, name='cerrar'),
    
    # Movimientos
    path('movimiento/nuevo/', views.nuevo_movimiento, name='nuevo_movimiento'),
    
    # Historial y reportes
    path('historial/', views.CajaListView.as_view(), name='historial'),
    path('detalle/<int:pk>/', views.CajaDetailView.as_view(), name='detalle'),
    
    # Informes y estadísticas
    path('informes/', views.informes_caja, name='informes'),
    path('informes/balance-general/', views.balance_general_ajax, name='balance_general_ajax'),
    path('informes/historial-arqueos/', views.historial_arqueos_ajax, name='historial_arqueos_ajax'),
    path('informes/flujo-efectivo/', views.flujo_efectivo_ajax, name='flujo_efectivo_ajax'),
    path('informes/detalle-caja/<int:caja_id>/', views.detalle_caja_modal_ajax, name='detalle_caja_modal_ajax'),
    
    # AJAX
    path('contar-efectivo/', views.contar_efectivo, name='contar_efectivo'),
    path('denominaciones/', views.obtener_denominaciones, name='denominaciones'),
    path('tipos-movimiento/', views.obtener_tipos_movimiento, name='tipos_movimiento'),
    path('estado-caja/', views.obtener_estado_caja, name='estado_caja'),
    path('ultimo-cierre/', views.obtener_ultimo_cierre, name='ultimo_cierre'),
    
    # ============================================================================
    # TESORERÍA
    # ============================================================================
    path('tesoreria/', views_tesoreria.tesoreria_dashboard, name='tesoreria_dashboard'),
    path('tesoreria/saldos/', views_tesoreria.get_saldos_tesoreria, name='tesoreria_saldos'),
    path('tesoreria/tipos-movimiento/', views_tesoreria.get_tipos_movimiento_tesoreria, name='tesoreria_tipos'),
    path('tesoreria/registrar-egreso/', views_tesoreria.registrar_egreso_tesoreria, name='tesoreria_registrar_egreso'),
    path('tesoreria/transferir-fondos/', views_tesoreria.transferir_fondos, name='tesoreria_transferir'),
    path('tesoreria/aplicar-balance/', views_tesoreria.aplicar_balance_cuentas, name='tesoreria_aplicar_balance'),
    
    # ============================================================================
    # ADMINISTRACIÓN AVANZADA (Solo Superusuarios)
    # ============================================================================
    # Importar las vistas admin
    path('admin/caja-completa/', lambda request: __import__('caja.admin_views', fromlist=['crear_caja_completa_admin']).crear_caja_completa_admin(request), name='crear_caja_completa_admin'),
    
    # Tesorería administrativa
    path('admin/transaccion-tesoreria/', lambda request: __import__('caja.tesoreria_admin_views', fromlist=['transaccion_tesoreria_admin']).transaccion_tesoreria_admin(request), name='transaccion_tesoreria_admin'),
    path('admin/gestor-tesoreria/', lambda request: __import__('caja.tesoreria_admin_views', fromlist=['gestor_tesoreria_admin']).gestor_tesoreria_admin(request), name='gestor_tesoreria_admin'),
    path('admin/validar-fondos/', lambda request: __import__('caja.tesoreria_admin_views', fromlist=['ajax_validar_fondos']).ajax_validar_fondos(request), name='ajax_validar_fondos'),
]