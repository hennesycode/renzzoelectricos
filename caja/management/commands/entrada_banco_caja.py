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
    help = 'Registra una entrada al banco desde la caja abierta'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que registra la entrada',
            required=True
        )
        parser.add_argument(
            '--tipo',
            type=str,
            help='Código del tipo de entrada (ej: VENTA, DEPOSITO, COBRO_CXC)',
        )
        parser.add_argument(
            '--monto',
            type=float,
            help='Monto a depositar en el banco',
        )
        parser.add_argument(
            '--referencia',
            type=str,
            help='Referencia opcional (se agregará automáticamente [BANCO])',
            default=''
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            help='Descripción opcional del movimiento',
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

        # Verificar que hay cuenta de banco activa
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        if not cuenta_banco:
            raise CommandError('❌ No hay cuenta de banco activa configurada.')

        # Mostrar información de la caja
        self.stdout.write('🏦 ENTRADA AL BANCO DESDE CAJA')
        self.stdout.write(f'📋 Caja Abierta: #{caja_abierta.id}')
        self.stdout.write(f'📅 Fecha apertura: {caja_abierta.fecha_apertura.date()}')
        self.stdout.write(f'👤 Usuario: {usuario.get_full_name() or usuario.username}')
        self.stdout.write(f'🏛️ Cuenta banco: {cuenta_banco.nombre}')
        self.stdout.write('=' * 60)
        self.stdout.write('ℹ️  Este registro sumará al total de Entradas Banco.')
        self.stdout.write('ℹ️  El sistema agregará automáticamente la etiqueta "BANCO".')
        self.stdout.write('=' * 60)

        # Determinar si usar modo interactivo o argumentos
        usar_interactivo = not all([
            options.get('tipo'),
            options.get('monto')
        ])

        if usar_interactivo:
            # Modo interactivo
            tipo_entrada, monto, referencia, descripcion = self._modo_interactivo()
        else:
            # Modo con argumentos
            tipo_entrada = options['tipo']
            monto = Decimal(str(options['monto']))
            referencia = options.get('referencia', '')
            descripcion = options.get('descripcion', '')

        # Validar tipo de entrada
        try:
            tipo_movimiento = TipoMovimiento.objects.get(codigo=tipo_entrada.upper())
        except TipoMovimiento.DoesNotExist:
            raise CommandError(f'❌ Tipo de entrada "{tipo_entrada}" no encontrado')

        # Validar que sea un tipo de ingreso
        if tipo_movimiento.tipo_base != 'INGRESO':
            raise CommandError(f'❌ "{tipo_movimiento.nombre}" no es un tipo de ingreso válido')

        # Validar monto
        if monto <= 0:
            raise CommandError('❌ El monto debe ser mayor a 0')

        # Agregar etiqueta [BANCO] a la descripción
        if descripcion:
            descripcion_final = f'[BANCO] {descripcion}'
        else:
            descripcion_final = f'[BANCO] Entrada al banco'

        # Preparar referencia con etiqueta BANCO
        if referencia:
            referencia_final = f'BANCO-{referencia}'
        else:
            referencia_final = ''

        # Mostrar resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMEN DE LA ENTRADA AL BANCO:')
        self.stdout.write(f'   🏷️ Tipo: {tipo_movimiento.nombre}')
        self.stdout.write(f'   💵 Monto: ${int(monto):,}')
        self.stdout.write(f'   📝 Descripción: {descripcion_final}')
        if referencia_final:
            self.stdout.write(f'   🔖 Referencia: {referencia_final}')
        self.stdout.write(f'   🏦 Destino: {cuenta_banco.nombre}')
        self.stdout.write('=' * 60)

        # Confirmación
        if usar_interactivo:
            confirmar = input('\n¿Confirma el registro de esta entrada al banco? (s/N): ')
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
                        descripcion=descripcion_final,
                        referencia=referencia_final,
                        usuario=usuario
                    )
                    
                    # Actualizar fecha manualmente
                    movimiento.fecha_movimiento = fecha_movimiento_tz
                    movimiento.save()

                    # Crear transacción en tesorería (va al banco)
                    transaccion = TransaccionGeneral.objects.create(
                        tipo='INGRESO',
                        monto=monto,
                        descripcion=f'Origen banco - Entrada:{tipo_movimiento.nombre} - {descripcion_final}',
                        referencia=referencia_final or f'MOV-{movimiento.id}',
                        tipo_movimiento=tipo_movimiento,
                        cuenta=cuenta_banco,
                        usuario=usuario
                    )
                    
                    # Actualizar fecha de la transacción también
                    transaccion.fecha = fecha_movimiento_tz
                    transaccion.save()

                    # Vincular movimiento y transacción
                    movimiento.transaccion_asociada = transaccion
                    movimiento.save()

                    # Actualizar saldo de la cuenta banco (sumar porque es ingreso)
                    cuenta_banco.saldo_actual += monto
                    cuenta_banco.save()
                    
                finally:
                    # Reconectar señales
                    post_save.connect(crear_transaccion_tesoreria_desde_movimiento, sender=MovimientoCaja)

                # Calcular saldo actual de caja y entradas banco
                saldo_caja = self._calcular_saldo_actual(caja_abierta)
                entradas_banco = self._calcular_entradas_banco(caja_abierta)

                self.stdout.write('\n✅ ENTRADA AL BANCO REGISTRADA EXITOSAMENTE')
                self.stdout.write(f'📋 Movimiento ID: {movimiento.id}')
                self.stdout.write(f'🏦 Transacción ID: {transaccion.id}')
                self.stdout.write(f'💵 Monto: ${int(monto):,}')
                self.stdout.write(f'🏛️ Cuenta destino: {cuenta_banco.nombre}')
                self.stdout.write(f'📊 Nuevo saldo banco: ${int(cuenta_banco.saldo_actual):,}')
                self.stdout.write(f'💰 Saldo disponible caja: ${int(saldo_caja):,}')
                self.stdout.write(f'🏦 Total entradas banco: ${int(entradas_banco):,}')

                self.stdout.write('\n🎉 Entrada al banco agregada y sincronizada!')

        except Exception as e:
            raise CommandError(f'❌ Error al crear la entrada al banco: {str(e)}')

    def _modo_interactivo(self):
        """Modo interactivo para obtener los datos de la entrada"""
        self.stdout.write('\n🏷️ TIPOS DE ENTRADA DISPONIBLES:')
        self.stdout.write('-' * 40)
        
        # Obtener tipos de ingreso
        tipos_ingreso = TipoMovimiento.objects.filter(
            activo=True,
            tipo_base='INGRESO'
        ).order_by('nombre')
        
        if not tipos_ingreso.exists():
            raise CommandError('❌ No hay tipos de ingreso configurados')
        
        # Mostrar opciones numeradas
        for idx, tipo in enumerate(tipos_ingreso, 1):
            self.stdout.write(f'   {idx}. {tipo.codigo} - {tipo.nombre}')
            if tipo.descripcion:
                self.stdout.write(f'      📝 {tipo.descripcion}')
        
        # Selección de tipo
        while True:
            try:
                opcion = input(f'\n¿Cuál tipo de entrada desea usar? (1-{tipos_ingreso.count()}): ')
                idx_seleccionado = int(opcion) - 1
                if 0 <= idx_seleccionado < tipos_ingreso.count():
                    tipo_seleccionado = list(tipos_ingreso)[idx_seleccionado]
                    break
                else:
                    self.stdout.write('❌ Opción inválida')
            except ValueError:
                self.stdout.write('❌ Ingrese un número válido')
        
        # Monto
        while True:
            try:
                monto_input = input('\n💵 Ingrese el monto a depositar: $')
                monto = Decimal(monto_input.replace(',', '').replace('$', ''))
                if monto > 0:
                    break
                else:
                    self.stdout.write('❌ El monto debe ser mayor a 0')
            except (ValueError, TypeError):
                self.stdout.write('❌ Ingrese un monto válido (solo números)')
        
        # Referencia (opcional)
        referencia = input('\n🔖 Referencia (opcional - se agregará "BANCO-"): ').strip()
        
        # Descripción (opcional)
        descripcion = input('\n📝 Descripción (opcional): ').strip()
        
        return tipo_seleccionado.codigo, monto, referencia, descripcion

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

    def _calcular_entradas_banco(self, caja):
        """Calcula el total de entradas al banco desde esta caja"""
        entradas_banco = MovimientoCaja.objects.filter(
            caja=caja,
            tipo='INGRESO',
            descripcion__icontains='[BANCO]'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        return entradas_banco