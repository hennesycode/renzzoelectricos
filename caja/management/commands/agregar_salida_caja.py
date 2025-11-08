from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.db import models
from decimal import Decimal
import pytz
from datetime import datetime
from caja.models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento, 
    TransaccionGeneral, Cuenta
)


class Command(BaseCommand):
    help = 'Agrega una salida (egreso) a la caja abierta'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que registra la salida',
            required=True
        )
        parser.add_argument(
            '--categoria',
            type=str,
            help='Código de la categoría de salida (ej: GASTO_GENERAL, PAGO_PROVEEDORES)',
        )
        parser.add_argument(
            '--monto',
            type=float,
            help='Monto de la salida en pesos',
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            help='Descripción del movimiento',
            default=''
        )
        parser.add_argument(
            '--referencia',
            type=str,
            help='Referencia opcional (factura, recibo, etc.)',
            default=''
        )

    def handle(self, *args, **options):
        # Obtener usuario
        User = get_user_model()
        try:
            usuario = User.objects.get(username=options['usuario'])
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{options["usuario"]}" no encontrado')

        # Verificar que hay una caja abierta
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
        if not caja_abierta:
            raise CommandError('❌ No hay ninguna caja abierta. Abra una caja primero.')

        # Mostrar información de la caja
        self.stdout.write('💰 AGREGAR SALIDA A CAJA')
        self.stdout.write(f'📋 Caja Abierta: #{caja_abierta.id}')
        self.stdout.write(f'📅 Fecha apertura: {caja_abierta.fecha_apertura.date()}')
        self.stdout.write(f'👤 Usuario: {usuario.get_full_name() or usuario.username}')
        self.stdout.write('=' * 60)

        # Determinar si usar modo interactivo o argumentos
        usar_interactivo = not all([
            options.get('categoria'),
            options.get('monto'),
            options.get('descripcion')
        ])

        if usar_interactivo:
            # Modo interactivo
            categoria, monto, descripcion, referencia = self._modo_interactivo()
        else:
            # Modo con argumentos
            categoria = options['categoria']
            monto = Decimal(str(options['monto']))
            descripcion = options['descripcion']
            referencia = options.get('referencia', '')

        # Validar categoría
        try:
            tipo_movimiento = TipoMovimiento.objects.get(codigo=categoria.upper())
        except TipoMovimiento.DoesNotExist:
            raise CommandError(f'❌ Categoría "{categoria}" no encontrada')

        # Validar monto
        if monto <= 0:
            raise CommandError('❌ El monto debe ser mayor a 0')

        # Verificar saldo suficiente en caja
        saldo_actual = self._calcular_saldo_actual(caja_abierta)
        if monto > saldo_actual:
            raise CommandError(f'❌ Saldo insuficiente en caja. Disponible: ${saldo_actual:,.0f}')

        # Mostrar resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMEN DE LA SALIDA:')
        self.stdout.write(f'   🏷️ Categoría: {tipo_movimiento.nombre}')
        self.stdout.write(f'   💸 Monto: ${int(monto):,}')
        self.stdout.write(f'   📝 Descripción: {descripcion}')
        if referencia:
            self.stdout.write(f'   🔖 Referencia: {referencia}')
        self.stdout.write('=' * 60)

        # Confirmación
        if usar_interactivo:
            confirmar = input('\n¿Confirma el registro de esta salida? (s/N): ')
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
                        tipo='EGRESO',
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
                        tipo='EGRESO',
                        monto=monto,
                        descripcion=f'Origen caja - Salida:{tipo_movimiento.nombre} - {descripcion}',
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

                    # Actualizar saldo de la cuenta destino (restar porque es egreso)
                    cuenta_destino.saldo_actual -= monto
                    cuenta_destino.save()
                    
                finally:
                    # Reconectar señales
                    post_save.connect(crear_transaccion_tesoreria_desde_movimiento, sender=MovimientoCaja)

                self.stdout.write('\n✅ SALIDA REGISTRADA EXITOSAMENTE')
                self.stdout.write(f'📋 Movimiento ID: {movimiento.id}')
                self.stdout.write(f'🏦 Transacción ID: {transaccion.id}')
                self.stdout.write(f'💸 Monto: ${int(monto):,}')
                self.stdout.write(f'🏛️ Cuenta origen: {cuenta_destino.nombre}')
                self.stdout.write(f'📊 Nuevo saldo cuenta: ${int(cuenta_destino.saldo_actual):,}')
                self.stdout.write(f'💰 Saldo disponible caja: ${int(self._calcular_saldo_actual(caja_abierta)):,}')

                self.stdout.write('\n🔥 Salida agregada y sincronizada con tesorería!')

        except Exception as e:
            raise CommandError(f'❌ Error al crear la salida: {str(e)}')

    def _modo_interactivo(self):
        """Modo interactivo para obtener los datos de la salida"""
        self.stdout.write('\n🏷️ CATEGORÍAS DE SALIDA DISPONIBLES:')
        self.stdout.write('-' * 40)
        
        # Obtener categorías de egreso/salida
        tipos_salida = TipoMovimiento.objects.filter(
            activo=True,
            tipo_base__in=['GASTO', 'INVERSION']
        ).order_by('nombre')
        
        if not tipos_salida.exists():
            raise CommandError('❌ No hay categorías de salida configuradas')
        
        # Mostrar opciones numeradas
        for idx, tipo in enumerate(tipos_salida, 1):
            self.stdout.write(f'   {idx}. {tipo.codigo} - {tipo.nombre}')
            if tipo.descripcion:
                self.stdout.write(f'      📝 {tipo.descripcion}')
        
        # Selección de categoría
        while True:
            try:
                opcion = input(f'\n¿Cuál categoría desea usar? (1-{tipos_salida.count()}): ')
                idx_seleccionado = int(opcion) - 1
                if 0 <= idx_seleccionado < tipos_salida.count():
                    tipo_seleccionado = list(tipos_salida)[idx_seleccionado]
                    break
                else:
                    self.stdout.write('❌ Opción inválida')
            except ValueError:
                self.stdout.write('❌ Ingrese un número válido')
        
        # Monto
        while True:
            try:
                monto_input = input('\n💸 Ingrese el monto de la salida: $')
                monto = Decimal(monto_input.replace(',', '').replace('$', ''))
                if monto > 0:
                    break
                else:
                    self.stdout.write('❌ El monto debe ser mayor a 0')
            except (ValueError, TypeError):
                self.stdout.write('❌ Ingrese un monto válido (solo números)')
        
        # Descripción
        descripcion = input('\n📝 Descripción del movimiento: ').strip()
        if not descripcion:
            descripcion = f'Salida - {tipo_seleccionado.nombre}'
        
        # Referencia (opcional)
        referencia = input('\n🔖 Referencia (opcional - Enter para omitir): ').strip()
        
        return tipo_seleccionado.codigo, monto, descripcion, referencia

    def _determinar_cuenta_destino(self, descripcion, tipo_movimiento):
        """Determina la cuenta destino según el tipo de movimiento"""
        # Si la descripción contiene [BANCO], va al banco
        if '[BANCO]' in descripcion.upper():
            cuenta = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
            if not cuenta:
                raise CommandError('❌ No hay cuenta de banco activa configurada')
            return cuenta
        
        # Para otros casos, usar cuenta de caja virtual
        cuenta_caja_virtual, created = Cuenta.objects.get_or_create(
            nombre='Caja Virtual',
            defaults={
                'tipo': 'RESERVA',
                'saldo_actual': Decimal('0.00'),
                'activo': False,
                'descripcion': 'Cuenta virtual para tracking de movimientos de caja'
            }
        )
        return cuenta_caja_virtual

    def _calcular_saldo_actual(self, caja):
        """Calcula el saldo actual de la caja"""
        ingresos = MovimientoCaja.objects.filter(
            caja=caja, 
            tipo='INGRESO'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        egresos = MovimientoCaja.objects.filter(
            caja=caja, 
            tipo='EGRESO'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        return ingresos - egresos