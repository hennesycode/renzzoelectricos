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
]
