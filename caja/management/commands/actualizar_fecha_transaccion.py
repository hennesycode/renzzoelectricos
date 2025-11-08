from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, date
import pytz
from caja.models import TransaccionGeneral


class Command(BaseCommand):
    help = 'Actualiza la fecha de una transacción específica de cierre de caja'

    def add_arguments(self, parser):
        parser.add_argument(
            '--referencia',
            type=str,
            help='Referencia de la transacción (ej: CIERRE-13)',
            required=True
        )
        parser.add_argument(
            '--nueva-fecha',
            type=str,
            help='Nueva fecha en formato DD/MM/AAAA (ej: 02/11/2025)',
            required=True
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            help='Parte de la descripción para confirmar la transacción (ej: paulaortegon)',
            default=''
        )

    def handle(self, *args, **options):
        referencia = options['referencia']
        nueva_fecha_str = options['nueva_fecha']
        descripcion_filtro = options.get('descripcion', '')

        # Validar formato de fecha
        try:
            nueva_fecha = datetime.strptime(nueva_fecha_str, '%d/%m/%Y').date()
        except ValueError:
            raise CommandError(f'Formato de fecha inválido. Use DD/MM/AAAA (ej: 02/11/2025)')

        self.stdout.write(f'\n🔍 BÚSQUEDA DE TRANSACCIÓN')
        self.stdout.write(f'📋 Referencia: {referencia}')
        self.stdout.write(f'📅 Nueva fecha: {nueva_fecha.strftime("%d/%m/%Y")}')
        if descripcion_filtro:
            self.stdout.write(f'📝 Filtro descripción: {descripcion_filtro}')
        self.stdout.write('=' * 60)

        # Buscar la transacción
        transacciones = TransaccionGeneral.objects.filter(referencia=referencia)
        
        if descripcion_filtro:
            transacciones = transacciones.filter(descripcion__icontains=descripcion_filtro)

        if not transacciones.exists():
            raise CommandError(f'No se encontró ninguna transacción con referencia "{referencia}"' + 
                             (f' y descripción que contenga "{descripcion_filtro}"' if descripcion_filtro else ''))

        if transacciones.count() > 1:
            self.stdout.write(f'⚠️ Se encontraron {transacciones.count()} transacciones:')
            for i, t in enumerate(transacciones, 1):
                self.stdout.write(f'   {i}. ID: {t.id} | Fecha: {t.fecha.strftime("%d/%m/%Y %H:%M")} | Usuario: {t.usuario.username}')
                self.stdout.write(f'      Descripción: {t.descripcion}')
                self.stdout.write(f'      Monto: ${int(t.monto):,}')
            raise CommandError('Múltiples transacciones encontradas. Sea más específico con el filtro.')

        transaccion = transacciones.first()

        # Mostrar información actual
        self.stdout.write('\n📊 TRANSACCIÓN ENCONTRADA:')
        self.stdout.write(f'   🆔 ID: {transaccion.id}')
        self.stdout.write(f'   📅 Fecha actual: {transaccion.fecha.strftime("%d/%m/%Y %H:%M:%S")}')
        self.stdout.write(f'   👤 Usuario: {transaccion.usuario.username}')
        self.stdout.write(f'   📋 Referencia: {transaccion.referencia}')
        self.stdout.write(f'   💰 Monto: ${int(transaccion.monto):,}')
        self.stdout.write(f'   📝 Descripción: {transaccion.descripcion}')
        self.stdout.write(f'   🏛️ Cuenta: {transaccion.cuenta.nombre}')

        # Crear nueva fecha con timezone Colombia manteniendo la hora actual
        colombia_tz = pytz.timezone('America/Bogota')
        hora_actual = transaccion.fecha.time()
        nueva_fecha_completa = colombia_tz.localize(
            datetime.combine(nueva_fecha, hora_actual)
        )

        self.stdout.write(f'\n🔄 CAMBIO A REALIZAR:')
        self.stdout.write(f'   📅 Fecha anterior: {transaccion.fecha.strftime("%d/%m/%Y %H:%M:%S")}')
        self.stdout.write(f'   📅 Fecha nueva: {nueva_fecha_completa.strftime("%d/%m/%Y %H:%M:%S")}')

        # Confirmación
        confirmar = input('\n¿Confirma la actualización de fecha? (s/N): ')
        if not confirmar.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            self.stdout.write('❌ Operación cancelada')
            return

        # Actualizar la fecha
        try:
            fecha_anterior = transaccion.fecha
            transaccion.fecha = nueva_fecha_completa
            transaccion.save(update_fields=['fecha'])

            self.stdout.write('\n✅ TRANSACCIÓN ACTUALIZADA EXITOSAMENTE')
            self.stdout.write(f'📋 ID: {transaccion.id}')
            self.stdout.write(f'📅 Fecha anterior: {fecha_anterior.strftime("%d/%m/%Y %H:%M:%S")}')
            self.stdout.write(f'📅 Fecha nueva: {transaccion.fecha.strftime("%d/%m/%Y %H:%M:%S")}')

        except Exception as e:
            raise CommandError(f'Error al actualizar la transacción: {str(e)}')

        self.stdout.write('\n🎉 Actualización completada exitosamente!')