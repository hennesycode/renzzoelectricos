from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from decimal import Decimal
import pytz
from datetime import datetime
from caja.models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento, 
    TransaccionGeneral, Cuenta
)


class Command(BaseCommand):
    help = 'Agrega una entrada (ingreso) a la caja abierta'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que registra la entrada',
            required=True
        )
        parser.add_argument(
            '--categoria',
            type=str,
            help='Código de la categoría/tipo de movimiento (ej: VENTA, COBRO_CXC, INGRESO)',
        )
        parser.add_argument(
            '--monto',
            type=str,
            help='Monto de la entrada (ej: 50000)',
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            help='Descripción del movimiento',
        )
        parser.add_argument(
            '--referencia',
            type=str,
            help='Referencia (número de factura, recibo, etc.)',
        )

    def handle(self, *args, **options):
        username = options['usuario']
        categoria_codigo = options.get('categoria')
        monto_str = options.get('monto')
        descripcion = options.get('descripcion')
        referencia = options.get('referencia')

        # Obtener usuario
        User = get_user_model()
        try:
            usuario = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{username}" no existe')

        # Verificar que haya una caja abierta
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
        if not caja_abierta:
            raise CommandError('No hay ninguna caja abierta. Abra una caja primero.')

        self.stdout.write(f'\n💰 AGREGAR ENTRADA A CAJA')
        self.stdout.write(f'📋 Caja Abierta: #{caja_abierta.id}')
        self.stdout.write(f'📅 Fecha apertura: {caja_abierta.fecha_apertura.date()}')
        self.stdout.write(f'👤 Usuario: {usuario.get_full_name() or usuario.username}')
        self.stdout.write('=' * 60)

        # Obtener tipos de movimiento disponibles para ingresos
        tipos_ingreso = TipoMovimiento.objects.filter(
            activo=True,
            tipo_base__in=['INGRESO', 'INTERNO']
        ).exclude(codigo='APERTURA').order_by('nombre')

        if not tipos_ingreso.exists():
            raise CommandError('No hay tipos de movimiento de ingreso configurados.')

        # Modo interactivo o con argumentos
        usar_interactivo = not all([categoria_codigo, monto_str, descripcion])

        if usar_interactivo:
            # Modo interactivo
            categoria_codigo, monto, descripcion, referencia = self._modo_interactivo(tipos_ingreso)
        else:
            # Modo con argumentos
            categoria_codigo, monto, descripcion, referencia = self._modo_argumentos(
                tipos_ingreso, categoria_codigo, monto_str, descripcion, referencia
            )

        # Obtener el tipo de movimiento
        try:
            tipo_movimiento = TipoMovimiento.objects.get(codigo=categoria_codigo, activo=True)
        except TipoMovimiento.DoesNotExist:
            raise CommandError(f'Tipo de movimiento "{categoria_codigo}" no existe o no está activo')

        # Mostrar resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'📊 RESUMEN DE LA ENTRADA:')
        self.stdout.write(f'   🏷️ Categoría: {tipo_movimiento.nombre}')
        self.stdout.write(f'   💵 Monto: ${int(monto):,}')
        self.stdout.write(f'   📝 Descripción: {descripcion}')
        if referencia:
            self.stdout.write(f'   🔖 Referencia: {referencia}')
        self.stdout.write('=' * 60)

        # Confirmación
        if usar_interactivo:
            confirmar = input('\n¿Confirma el registro de esta entrada? (s/N): ')
            if confirmar.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                self.stdout.write('❌ Operación cancelada')
                return

        # Crear el movimiento
        try:
            # Obtener fecha de la caja (convertir a timezone de Colombia)
            colombia_tz = pytz.timezone('America/Bogota')
            fecha_caja = caja_abierta.fecha_apertura.astimezone(colombia_tz).date()
            fecha_movimiento = datetime.combine(fecha_caja, datetime.now(colombia_tz).time())
            fecha_movimiento_tz = colombia_tz.localize(fecha_movimiento)

            with transaction.atomic():
                # Desconectar señales para evitar duplicación
                from caja.models import crear_transaccion_tesoreria_desde_movimiento
                post_save.disconnect(crear_transaccion_tesoreria_desde_movimiento, sender=MovimientoCaja)
                
                try:
                    # Crear movimiento en la caja con fecha correcta
                    movimiento = MovimientoCaja.objects.create(
                        caja=caja_abierta,
                        tipo_movimiento=tipo_movimiento,
                        tipo='INGRESO',
                        monto=monto,
                        descripcion=descripcion,
                        referencia=referencia or '',
                        usuario=usuario
                    )
                    
                    # Actualizar fecha manualmente
                    movimiento.fecha_movimiento = fecha_movimiento_tz
                    movimiento.save()

                    # Crear transacción en tesorería
                    cuenta_destino = self._determinar_cuenta_destino(descripcion, tipo_movimiento)

                    transaccion = TransaccionGeneral.objects.create(
                        tipo='INGRESO',
                        monto=monto,
                        descripcion=f'Origen caja - Entrada:{tipo_movimiento.nombre} - {descripcion}',
                        referencia=referencia or f'MOV-{movimiento.id}',
                        tipo_movimiento=tipo_movimiento,
                        cuenta=cuenta_destino,
                        usuario=usuario
                    )
                    
                    # Actualizar fecha de la transacción también
                    transaccion.fecha = fecha_movimiento_tz
                    transaccion.save()

                    # Vincular movimiento y transacción
                    movimiento.transaccion_asociada = transaccion
                    movimiento.save()

                    # Actualizar saldo de la cuenta destino
                    cuenta_destino.saldo_actual += monto
                    cuenta_destino.save()
                    
                finally:
                    # Reconectar señales
                    post_save.connect(crear_transaccion_tesoreria_desde_movimiento, sender=MovimientoCaja)

                self.stdout.write('\n✅ ENTRADA REGISTRADA EXITOSAMENTE')
                self.stdout.write(f'📋 Movimiento ID: {movimiento.id}')
                self.stdout.write(f'🏦 Transacción ID: {transaccion.id}')
                self.stdout.write(f'💰 Monto: ${int(monto):,}')
                self.stdout.write(f'🏛️ Cuenta destino: {cuenta_destino.nombre}')
                self.stdout.write(f'📊 Nuevo saldo cuenta: ${int(cuenta_destino.saldo_actual):,}')

        except Exception as e:
            raise CommandError(f'Error al registrar la entrada: {str(e)}')

        self.stdout.write('\n🎉 Entrada agregada y sincronizada con tesorería!')

    def _modo_interactivo(self, tipos_ingreso):
        """Modo interactivo que pide todos los datos"""
        
        # Mostrar categorías disponibles
        self.stdout.write('\n🏷️ CATEGORÍAS DISPONIBLES:')
        self.stdout.write('-' * 40)
        for i, tipo in enumerate(tipos_ingreso, 1):
            self.stdout.write(f'   {i}. {tipo.codigo} - {tipo.nombre}')
            if tipo.descripcion:
                self.stdout.write(f'      📝 {tipo.descripcion}')

        # Seleccionar categoría
        while True:
            try:
                seleccion = input(f'\n¿Cuál categoría desea usar? (1-{tipos_ingreso.count()}): ')
                index = int(seleccion) - 1
                if 0 <= index < tipos_ingreso.count():
                    categoria_codigo = tipos_ingreso[index].codigo
                    break
                else:
                    self.stdout.write('❌ Selección inválida')
            except (ValueError, EOFError):
                self.stdout.write('❌ Ingrese un número válido')

        # Obtener monto
        while True:
            try:
                monto_str = input('\n💵 Ingrese el monto de la entrada: $')
                monto = Decimal(monto_str.replace(',', '').replace('.', ''))
                if monto <= 0:
                    self.stdout.write('❌ El monto debe ser mayor a cero')
                    continue
                break
            except (ValueError, EOFError):
                self.stdout.write('❌ Ingrese un monto válido (solo números)')

        # Obtener descripción
        while True:
            try:
                descripcion = input('\n📝 Descripción del movimiento: ').strip()
                if descripcion:
                    break
                else:
                    self.stdout.write('❌ La descripción es obligatoria')
            except EOFError:
                self.stdout.write('❌ Error en la entrada')
                raise CommandError('Modo interactivo interrumpido')

        # Obtener referencia (opcional)
        try:
            referencia = input('\n🔖 Referencia (opcional - Enter para omitir): ').strip()
        except EOFError:
            referencia = ''

        return categoria_codigo, monto, descripcion, referencia

    def _modo_argumentos(self, tipos_ingreso, categoria_codigo, monto_str, descripcion, referencia):
        """Modo con argumentos predefinidos"""
        
        # Validar categoría
        if not tipos_ingreso.filter(codigo=categoria_codigo).exists():
            codigos_validos = ', '.join([t.codigo for t in tipos_ingreso])
            raise CommandError(f'Categoría "{categoria_codigo}" no válida. Opciones: {codigos_validos}')

        # Validar monto
        try:
            monto = Decimal(monto_str.replace(',', '').replace('.', ''))
            if monto <= 0:
                raise CommandError('El monto debe ser mayor a cero')
        except (ValueError, TypeError):
            raise CommandError('Monto inválido. Use solo números.')

        # Validar descripción
        if not descripcion or not descripcion.strip():
            raise CommandError('La descripción es obligatoria')

        return categoria_codigo, monto, descripcion.strip(), referencia or ''

    def _determinar_cuenta_destino(self, descripcion, tipo_movimiento):
        """Determina la cuenta destino según el tipo de movimiento y descripción"""
        
        # Si es entrada al banco (contiene [BANCO])
        if '[BANCO]' in descripcion.upper():
            cuenta = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
            if cuenta:
                return cuenta

        # Usar cuenta "Caja Virtual" por defecto para movimientos de caja
        cuenta_caja, created = Cuenta.objects.get_or_create(
            nombre='Caja Virtual',
            defaults={
                'tipo': 'RESERVA',
                'saldo_actual': Decimal('0.00'),
                'activo': False
            }
        )
        
        return cuenta_caja