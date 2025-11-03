"""
Vistas para el sistema de facturación.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def facturacion_index(request):
    """
    Vista principal del módulo de facturación.
    Muestra la interfaz para generar facturas.
    """
    return render(request, 'facturacion/index.html')

