"""
URLs para el sistema de caja registradora.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.urls import path
from . import views

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
]