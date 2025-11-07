from django.db import migrations


def create_default_tipos(apps, schema_editor):
    """
    Crea los tipos de movimiento por defecto que deben existir en todos los servidores.
    """
    TipoMovimiento = apps.get_model('caja', 'TipoMovimiento')

    # Tipos de INGRESO (en el orden especificado)
    tipos_ingreso = [
        ('VENTA', 'Venta'),
        ('COBRO_CXC', 'Cobro de Cuentas por Cobrar'),
        ('DEV_PAGO', 'Devolución de un Pago'),
        ('REC_GASTOS', 'Recuperación de Gastos'),
    ]

    # Tipos de EGRESO (en el orden especificado)
    tipos_egreso = [
        ('GASTO', 'Gasto general'),
        ('COMPRA', 'Compra de Mercadería'),
        ('FLETES', 'Fletes y Transporte'),
        ('DEV_VENTA', 'Devolución de Venta'),
        ('SUELDOS', 'Sueldos y Salarios'),
        ('SUMINISTROS', 'Suministros'),
        ('ALQUILER', 'Alquiler y Servicios'),
        ('MANTENIMIENTO', 'Mantenimiento y Reparaciones'),
    ]

    # Tipo especial para apertura
    tipos_especiales = [
        ('APERTURA', 'Apertura'),
    ]

    # Crear o actualizar todos los tipos
    for codigo, nombre in (tipos_ingreso + tipos_egreso + tipos_especiales):
        TipoMovimiento.objects.update_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'descripcion': '', 'activo': True}
        )


def deactivate_default_tipos(apps, schema_editor):
    """
    Función reversa: desactiva los tipos por defecto en lugar de eliminarlos.
    """
    TipoMovimiento = apps.get_model('caja', 'TipoMovimiento')
    
    codigos_default = [
        'VENTA', 'COBRO_CXC', 'DEV_PAGO', 'REC_GASTOS',
        'GASTO', 'COMPRA', 'FLETES', 'DEV_VENTA', 'SUELDOS', 
        'SUMINISTROS', 'ALQUILER', 'MANTENIMIENTO', 'APERTURA'
    ]
    
    TipoMovimiento.objects.filter(codigo__in=codigos_default).update(activo=False)


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0006_alter_tipomovimiento_codigo_max_length'),
    ]

    operations = [
        migrations.RunPython(create_default_tipos, deactivate_default_tipos),
    ]
