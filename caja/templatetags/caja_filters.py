"""
Filtros personalizados para templates de Caja.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='formato_pesos_colombia')
def formato_pesos_colombia(valor):
    """
    Formatea un valor numérico en formato de pesos colombianos
    con separadores de miles (punto) sin decimales.
    
    Ejemplo: 190000 -> "190.000"
             1500000 -> "1.500.000"
    """
    try:
        # Convertir a float si es Decimal
        if isinstance(valor, Decimal):
            valor = float(valor)
        
        # Redondear a entero
        valor = int(round(valor))
        
        # Formatear con separadores de miles
        return "{:,}".format(valor).replace(",", ".")
    except (ValueError, TypeError):
        return "0"
