from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db import models
from decimal import Decimal
import pytz
from datetime import datetime
from caja.models import (
    CajaRegistradora, TipoMovimiento, 
    TransaccionGeneral, Cuenta
)


class Command(BaseCommand):
    help = 'Registra un gasto directo en tesorería (Banco o Reserva)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que registra el gasto',
            required=True
        )
        parser.add_argument(
            '--origen',
            type=str,
            help='Origen de fondos: BANCO o RESERVA',
        )
        parser.add_argument(
            '--categoria',
            type=str,
            help='Código de la categoría de gasto (ej: GASTO, EQUIPOS, SERVICIOS)',
        )
        parser.add_argument(
            '--monto',
            type=float,
            help='Monto del gasto',
        )
        parser.add_argument(
            '--referencia',
            type=str,
            help='Referencia opcional (factura, recibo, etc.)',
            default=''
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            help='Descripción del gasto',
            default=''
        )

    def handle(self, *args, **options):
        # Obtener usuario
        User = get_user_model()
        try:
            usuario = User.objects.get(username=options['usuario'])
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{options["usuario"]}" no encontrado')

        # Obtener fecha de referencia (de la caja abierta si existe)
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
        if caja_abierta:
            fecha_referencia = caja_abierta.fecha_apertura.date()
            self.stdout.write(f'📅 Usando fecha de caja abierta: {fecha_referencia}')
        else:
            # Si no hay caja abierta, usar fecha actual
            fecha_referencia = datetime.now().date()
            self.stdout.write(f'📅 No hay caja abierta, usando fecha actual: {fecha_referencia}')

        # Mostrar información
        self.stdout.write('💸 REGISTRAR GASTO DE TESORERÍA')
        self.stdout.write(f'👤 Usuario: {usuario.get_full_name() or usuario.username}')
        self.stdout.write('=' * 60)
        self.stdout.write('ℹ️  Este gasto se registrará directamente en tesorería.')
        self.stdout.write('ℹ️  Se descontará del origen de fondos seleccionado.')
        self.stdout.write('=' * 60)

        # Determinar si usar modo interactivo o argumentos
        usar_interactivo = not all([
            options.get('origen'),
            options.get('categoria'),
            options.get('monto'),
            options.get('descripcion')
        ])

        if usar_interactivo:
            # Modo interactivo
            cuenta_origen, tipo_movimiento, monto, referencia, descripcion = self._modo_interactivo()
        else:
            # Modo con argumentos
            # Validar origen
            origen = options['origen'].upper()
            if origen not in ['BANCO', 'RESERVA']:
                raise CommandError('❌ Origen debe ser BANCO o RESERVA')
            
            cuenta_origen = Cuenta.objects.filter(tipo=origen, activo=True).first()
            if not cuenta_origen:
                raise CommandError(f'❌ No hay cuenta {origen.lower()} activa')

            # Validar categoría
            try:
                tipo_movimiento = TipoMovimiento.objects.get(codigo=options['categoria'].upper())
            except TipoMovimiento.DoesNotExist:
                raise CommandError(f'❌ Categoría "{options["categoria"]}" no encontrada')

            monto = Decimal(str(options['monto']))
            referencia = options.get('referencia', '')
            descripcion = options['descripcion']

        # Validar que sea un tipo de gasto/inversión
        if tipo_movimiento.tipo_base not in ['GASTO', 'INVERSION']:
            raise CommandError(f'❌ "{tipo_movimiento.nombre}" no es un tipo de gasto válido')

        # Validar monto
        if monto <= 0:
            raise CommandError('❌ El monto debe ser mayor a 0')

        # Validar saldo suficiente
        if monto > cuenta_origen.saldo_actual:
            raise CommandError(f'❌ Saldo insuficiente en {cuenta_origen.nombre}. Disponible: ${cuenta_origen.saldo_actual:,.0f}')

        # Mostrar resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMEN DEL GASTO:')
        self.stdout.write(f'   🏦 Origen: {cuenta_origen.nombre}')
        self.stdout.write(f'   🏷️ Categoría: {tipo_movimiento.nombre}')
        self.stdout.write(f'   💸 Monto: ${int(monto):,}')
        self.stdout.write(f'   📝 Descripción: {descripcion}')
        if referencia:
            self.stdout.write(f'   🔖 Referencia: {referencia}')
        self.stdout.write(f'   📅 Fecha: {fecha_referencia}')
        self.stdout.write('=' * 60)

        # Confirmación
        if usar_interactivo:
            confirmar = input('\n¿Confirma el registro de este gasto? (s/N): ')
            if confirmar.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                self.stdout.write('❌ Operación cancelada')
                return

        # Crear la transacción
        try:
            # Obtener fecha con hora actual pero del día de referencia
            colombia_tz = pytz.timezone('America/Bogota')
            fecha_gasto = datetime.combine(fecha_referencia, datetime.now(colombia_tz).time())
            fecha_gasto_tz = colombia_tz.localize(fecha_gasto)

            with transaction.atomic():
                # Crear transacción de gasto
                transaccion = TransaccionGeneral.objects.create(
                    tipo='EGRESO',
                    monto=monto,
                    descripcion=descripcion,
                    referencia=referencia,
                    tipo_movimiento=tipo_movimiento,
                    cuenta=cuenta_origen,
                    usuario=usuario
                )
                
                # Actualizar fecha manualmente
                transaccion.fecha = fecha_gasto_tz
                transaccion.save()

                # Actualizar saldo de la cuenta origen (restar porque es egreso)
                cuenta_origen.saldo_actual -= monto
                cuenta_origen.save()

                self.stdout.write('\n✅ GASTO REGISTRADO EXITOSAMENTE')
                self.stdout.write(f'🏦 Transacción ID: {transaccion.id}')
                self.stdout.write(f'💸 Monto: ${int(monto):,}')
                self.stdout.write(f'🏛️ Cuenta origen: {cuenta_origen.nombre}')
                self.stdout.write(f'📊 Nuevo saldo: ${int(cuenta_origen.saldo_actual):,}')
                self.stdout.write(f'📅 Fecha: {fecha_gasto_tz.strftime("%d/%m/%Y %H:%M")}')

                self.stdout.write('\n🎉 Gasto de tesorería registrado correctamente!')

        except Exception as e:
            raise CommandError(f'❌ Error al crear el gasto: {str(e)}')

    def _modo_interactivo(self):
        """Modo interactivo para obtener los datos del gasto"""        
        # Selección de origen de fondos
        self.stdout.write('\n🏦 ORIGEN DE FONDOS:')
        self.stdout.write('-' * 40)
        
        cuentas_disponibles = Cuenta.objects.filter(activo=True).order_by('tipo', 'nombre')
        if not cuentas_disponibles.exists():
            raise CommandError('❌ No hay cuentas activas disponibles')
        
        # Mostrar cuentas disponibles
        for idx, cuenta in enumerate(cuentas_disponibles, 1):
            if cuenta.tipo == 'BANCO':
                tipo_emoji = '🏦'
            elif 'guardado' in cuenta.nombre.lower():
                tipo_emoji = '💵'
            else:
                tipo_emoji = '💰'
            self.stdout.write(f'   {idx}. {tipo_emoji} {cuenta.nombre}')
            self.stdout.write(f'      Saldo disponible: ${cuenta.saldo_actual:,.0f}')
        
        # Selección de cuenta
        while True:
            try:
                opcion = input(f'\n¿De qué cuenta desea realizar el gasto? (1-{cuentas_disponibles.count()}): ')
                idx_seleccionado = int(opcion) - 1
                if 0 <= idx_seleccionado < cuentas_disponibles.count():
                    cuenta_seleccionada = list(cuentas_disponibles)[idx_seleccionado]
                    break
                else:
                    self.stdout.write('❌ Opción inválida')
            except ValueError:
                self.stdout.write('❌ Ingrese un número válido')

        # Selección de categoría de gasto
        self.stdout.write('\n🏷️ CATEGORÍAS DE GASTO DISPONIBLES:')
        self.stdout.write('-' * 40)
        
        tipos_gasto = TipoMovimiento.objects.filter(
            activo=True,
            tipo_base__in=['GASTO', 'INVERSION']
        ).order_by('tipo_base', 'nombre')
        
        if not tipos_gasto.exists():
            raise CommandError('❌ No hay categorías de gasto configuradas')
        
        # Mostrar categorías por tipo
        tipo_actual = None
        for idx, tipo in enumerate(tipos_gasto, 1):
            if tipo.tipo_base != tipo_actual:
                tipo_actual = tipo.tipo_base
                emoji = '💸' if tipo_actual == 'GASTO' else '🔧'
                self.stdout.write(f'\n   {emoji} {tipo_actual}:')
            
            self.stdout.write(f'   {idx}. {tipo.codigo} - {tipo.nombre}')
            if tipo.descripcion:
                self.stdout.write(f'      📝 {tipo.descripcion}')
        
        # Selección de categoría
        while True:
            try:
                opcion = input(f'\n¿Cuál categoría desea usar? (1-{tipos_gasto.count()}): ')
                idx_seleccionado = int(opcion) - 1
                if 0 <= idx_seleccionado < tipos_gasto.count():
                    tipo_seleccionado = list(tipos_gasto)[idx_seleccionado]
                    break
                else:
                    self.stdout.write('❌ Opción inválida')
            except ValueError:
                self.stdout.write('❌ Ingrese un número válido')
        
        # Monto
        while True:
            try:
                monto_input = input('\n💸 Ingrese el monto del gasto: $')
                monto = Decimal(monto_input.replace(',', '').replace('$', ''))
                if monto > 0:
                    if monto <= cuenta_seleccionada.saldo_actual:
                        break
                    else:
                        self.stdout.write(f'❌ Saldo insuficiente. Disponible: ${cuenta_seleccionada.saldo_actual:,.0f}')
                else:
                    self.stdout.write('❌ El monto debe ser mayor a 0')
            except (ValueError, TypeError):
                self.stdout.write('❌ Ingrese un monto válido (solo números)')
        
        # Descripción
        descripcion = input('\n📝 Descripción del gasto: ').strip()
        if not descripcion:
            descripcion = f'Gasto - {tipo_seleccionado.nombre}'
        
        # Referencia (opcional)
        referencia = input('\n🔖 Referencia (opcional - Enter para omitir): ').strip()
        
        return cuenta_seleccionada, tipo_seleccionado, monto, referencia, descripcion