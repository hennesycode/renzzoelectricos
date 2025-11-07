"""
Management command para registrar gastos del banco de manera interactiva.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from caja.models import Cuenta, TipoMovimiento, TransaccionGeneral
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Registra un gasto del banco de manera interactiva'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha del gasto (formato: YYYY-MM-DD, por defecto hoy)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== REGISTRO DE GASTO DEL BANCO ===\n')
        )

        try:
            # 1. Seleccionar fecha
            fecha = self._obtener_fecha(options.get('fecha'))
            
            # 2. Seleccionar origen de fondos (cuenta bancaria)
            cuenta = self._seleccionar_cuenta()
            
            # 3. Seleccionar categoría (tipo de movimiento)
            tipo_movimiento = self._seleccionar_categoria()
            
            # 4. Ingresar monto
            monto = self._ingresar_monto()
            
            # 5. Verificar saldo disponible
            if not self._verificar_saldo(cuenta, monto):
                return
            
            # 6. Ingresar referencia (opcional)
            referencia = self._ingresar_referencia()
            
            # 7. Ingresar descripción
            descripcion = self._ingresar_descripcion()
            
            # 8. Mostrar resumen y confirmar
            if self._confirmar_transaccion(fecha, cuenta, tipo_movimiento, monto, referencia, descripcion):
                self._registrar_gasto(fecha, cuenta, tipo_movimiento, monto, referencia, descripcion)
            else:
                self.stdout.write(self.style.WARNING('Operación cancelada por el usuario.'))

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nOperación cancelada por el usuario.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def _obtener_fecha(self, fecha_str):
        """Obtiene la fecha para el gasto."""
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                self.stdout.write(f'Fecha seleccionada: {fecha.strftime("%d/%m/%Y")}')
                return fecha
            except ValueError:
                self.stdout.write(self.style.ERROR('Formato de fecha inválido. Usando fecha de hoy.'))
        
        # Usar fecha de hoy por defecto
        hoy = timezone.now().date()
        
        # Preguntar si quiere usar hoy o cambiar la fecha
        respuesta = input(f'¿Usar fecha de hoy ({hoy.strftime("%d/%m/%Y")})? (s/n) [s]: ').strip().lower()
        
        if respuesta in ['n', 'no']:
            while True:
                fecha_input = input('Ingrese la fecha (DD/MM/YYYY): ').strip()
                try:
                    fecha = datetime.strptime(fecha_input, '%d/%m/%Y').date()
                    self.stdout.write(f'Fecha seleccionada: {fecha.strftime("%d/%m/%Y")}')
                    return fecha
                except ValueError:
                    self.stdout.write(self.style.ERROR('Formato inválido. Use DD/MM/YYYY'))
        
        self.stdout.write(f'Usando fecha de hoy: {hoy.strftime("%d/%m/%Y")}')
        return hoy

    def _seleccionar_cuenta(self):
        """Permite seleccionar la cuenta bancaria de origen."""
        self.stdout.write('\n--- ORIGEN DE FONDOS ---')
        
        # Obtener solo cuentas bancarias activas
        cuentas_banco = Cuenta.objects.filter(
            tipo=Cuenta.TipoCuentaChoices.BANCO,
            activo=True
        ).order_by('nombre')
        
        if not cuentas_banco.exists():
            raise CommandError('No hay cuentas bancarias disponibles. Ejecute primero: python manage.py crear_cuentas_tesoreria')
        
        self.stdout.write('Cuentas bancarias disponibles:')
        for i, cuenta in enumerate(cuentas_banco, 1):
            self.stdout.write(f'{i}. {cuenta.nombre} - Saldo: ${cuenta.saldo_actual:,.2f}')
        
        while True:
            try:
                opcion = int(input('\nSeleccione el número de cuenta: ')) - 1
                if 0 <= opcion < len(cuentas_banco):
                    cuenta_seleccionada = cuentas_banco[opcion]
                    self.stdout.write(f'Cuenta seleccionada: {cuenta_seleccionada.nombre}')
                    return cuenta_seleccionada
                else:
                    self.stdout.write(self.style.ERROR('Opción inválida.'))
            except ValueError:
                self.stdout.write(self.style.ERROR('Ingrese un número válido.'))

    def _seleccionar_categoria(self):
        """Permite seleccionar la categoría del gasto."""
        self.stdout.write('\n--- CATEGORÍA ---')
        
        # Obtener tipos de movimiento de gasto/inversión activos
        tipos_gasto = TipoMovimiento.objects.filter(
            activo=True,
            tipo_base__in=[TipoMovimiento.TipoBaseChoices.GASTO, TipoMovimiento.TipoBaseChoices.INVERSION]
        ).order_by('tipo_base', 'nombre')
        
        if not tipos_gasto.exists():
            raise CommandError('No hay categorías de gasto disponibles. Ejecute primero: python manage.py crear_tipos_defecto')
        
        self.stdout.write('Categorías disponibles:')
        
        # Agrupar por tipo base
        gasto_operativo = tipos_gasto.filter(tipo_base=TipoMovimiento.TipoBaseChoices.GASTO)
        inversiones = tipos_gasto.filter(tipo_base=TipoMovimiento.TipoBaseChoices.INVERSION)
        
        contador = 1
        opciones = []
        
        if gasto_operativo.exists():
            self.stdout.write('\n  GASTOS OPERATIVOS:')
            for tipo in gasto_operativo:
                self.stdout.write(f'  {contador}. {tipo.nombre}')
                opciones.append(tipo)
                contador += 1
        
        if inversiones.exists():
            self.stdout.write('\n  COMPRAS / INVERSIONES:')
            for tipo in inversiones:
                self.stdout.write(f'  {contador}. {tipo.nombre}')
                opciones.append(tipo)
                contador += 1
        
        while True:
            try:
                opcion = int(input('\nSeleccione el número de categoría: ')) - 1
                if 0 <= opcion < len(opciones):
                    tipo_seleccionado = opciones[opcion]
                    self.stdout.write(f'Categoría seleccionada: {tipo_seleccionado.nombre}')
                    return tipo_seleccionado
                else:
                    self.stdout.write(self.style.ERROR('Opción inválida.'))
            except ValueError:
                self.stdout.write(self.style.ERROR('Ingrese un número válido.'))

    def _ingresar_monto(self):
        """Permite ingresar el monto del gasto."""
        self.stdout.write('\n--- MONTO ---')
        
        while True:
            monto_input = input('Ingrese el monto del gasto ($): ').strip().replace('$', '').replace(',', '')
            try:
                monto = Decimal(monto_input)
                if monto <= 0:
                    self.stdout.write(self.style.ERROR('El monto debe ser mayor a cero.'))
                    continue
                
                # Confirmar monto
                confirmacion = input(f'Monto: ${monto:,.2f} ¿Es correcto? (s/n) [s]: ').strip().lower()
                if confirmacion in ['', 's', 'si', 'sí']:
                    return monto
                
            except (InvalidOperation, ValueError):
                self.stdout.write(self.style.ERROR('Monto inválido. Ingrese solo números.'))

    def _verificar_saldo(self, cuenta, monto):
        """Verifica si hay saldo suficiente en la cuenta."""
        if cuenta.saldo_actual < monto:
            self.stdout.write(
                self.style.ERROR(
                    f'\nSaldo insuficiente en {cuenta.nombre}:\n'
                    f'  Disponible: ${cuenta.saldo_actual:,.2f}\n'
                    f'  Requerido: ${monto:,.2f}\n'
                    f'  Faltante: ${monto - cuenta.saldo_actual:,.2f}'
                )
            )
            return False
        return True

    def _ingresar_referencia(self):
        """Permite ingresar una referencia opcional."""
        self.stdout.write('\n--- REFERENCIA (Opcional) ---')
        referencia = input('Ej: Factura #123, Comprobante #456, etc.: ').strip()
        
        if referencia:
            self.stdout.write(f'Referencia: {referencia}')
        else:
            self.stdout.write('Sin referencia')
        
        return referencia

    def _ingresar_descripcion(self):
        """Permite ingresar la descripción del gasto."""
        self.stdout.write('\n--- DESCRIPCIÓN ---')
        
        while True:
            descripcion = input('Describa el gasto: ').strip()
            if descripcion:
                return descripcion
            else:
                self.stdout.write(self.style.ERROR('La descripción es obligatoria.'))

    def _confirmar_transaccion(self, fecha, cuenta, tipo_movimiento, monto, referencia, descripcion):
        """Muestra un resumen y solicita confirmación final."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DEL GASTO'))
        self.stdout.write('='*60)
        self.stdout.write(f'Fecha: {fecha.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Origen: {cuenta.nombre}')
        self.stdout.write(f'Categoría: {tipo_movimiento.nombre}')
        self.stdout.write(f'Monto: ${monto:,.2f}')
        if referencia:
            self.stdout.write(f'Referencia: {referencia}')
        self.stdout.write(f'Descripción: {descripcion}')
        self.stdout.write(f'\nSaldo actual: ${cuenta.saldo_actual:,.2f}')
        self.stdout.write(f'Saldo después: ${cuenta.saldo_actual - monto:,.2f}')
        self.stdout.write('='*60)
        
        confirmacion = input('\n¿Confirmar el registro del gasto? (s/n): ').strip().lower()
        return confirmacion in ['s', 'si', 'sí']

    def _registrar_gasto(self, fecha, cuenta, tipo_movimiento, monto, referencia, descripcion):
        """Registra el gasto en la base de datos."""
        try:
            with transaction.atomic():
                # Crear la transacción
                transaccion = TransaccionGeneral.objects.create(
                    fecha=timezone.make_aware(
                        datetime.combine(fecha, datetime.min.time())
                    ),
                    tipo=TransaccionGeneral.TipoTransaccionChoices.EGRESO,
                    monto=monto,
                    descripcion=descripcion,
                    referencia=referencia,
                    tipo_movimiento=tipo_movimiento,
                    cuenta=cuenta,
                    usuario=None  # Podríamos agregar el usuario si es necesario
                )
                
                # Actualizar saldo de la cuenta
                cuenta.saldo_actual -= monto
                cuenta.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Gasto registrado exitosamente!\n'
                        f'  ID Transacción: {transaccion.id}\n'
                        f'  Nuevo saldo en {cuenta.nombre}: ${cuenta.saldo_actual:,.2f}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al registrar el gasto: {str(e)}')
            )
            raise