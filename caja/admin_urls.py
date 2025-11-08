"""
URLs específicas para funciones administrativas avanzadas de caja.
"""
from django.urls import path
from . import admin_views

app_name = 'caja_admin'

urlpatterns = [
    # Crear caja completa con fecha personalizada (solo superusuarios)
    path('crear-caja-completa/', admin_views.crear_caja_completa_admin, name='crear_caja_completa'),
    
    # Resumen detallado de caja (solo superusuarios)
    path('resumen-caja/<int:caja_id>/', admin_views.resumen_caja_admin, name='resumen_caja'),
]