"""
URLs para el sistema de facturación.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    # Vista principal de facturación
    path('', views.facturacion_index, name='index'),
    
    # AJAX endpoints
    path('ajax/listar-clientes/', views.listar_clientes_ajax, name='listar_clientes_ajax'),
    path('ajax/crear-cliente/', views.crear_cliente_ajax, name='crear_cliente_ajax'),
    path('ajax/buscar-productos/', views.buscar_productos_ajax, name='buscar_productos_ajax'),
    path('ajax/guardar-factura/', views.guardar_factura_ajax, name='guardar_factura_ajax'),
]
