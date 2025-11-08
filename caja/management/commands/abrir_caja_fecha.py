from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
from caja.models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento, 
    DenominacionMoneda, ConteoEfectivo, DetalleConteo, Cuenta
)
import re


class Command(BaseCommand):
    help = 'Abre una caja registradora en una fecha específica con denominaciones detalladas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha de apertura en formato DD/MM/AAAA (ej: 15/03/2024)',
            required=True
        )
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que abre la caja',
            required=True
        )
        parser.add_argument(
            '--billetes',
            type=str,
            help='Cantidades de billetes separadas por comas en orden: 100k,50k,20k,10k,5k,2k,1k (ej: 1,2,0,0,0,0,0)',
            default='0,0,0,0,0,0,0'
        )
        parser.add_argument(
            '--monedas',
            type=str,
            help='Cantidades de monedas separadas por comas en orden: 1k,500,200,100,50 (ej: 0,0,0,0,0)',
            default='0,0,0,0,0'
        )
        parser.add_argument(
            '--interactivo',
            action='store_true',
            help='Modo interactivo (pregunta por cada denominación)'
        )

    def handle(self, *args, **options):
        fecha_str = options['fecha']
        username = options['usuario']
        billetes_str = options['billetes']
        monedas_str = options['monedas']
        interactivo = options['interactivo']

        # Validar formato de fecha
        try:
            fecha_apertura = datetime.strptime(fecha_str, '%d/%m/%Y').date()
        except ValueError:
            raise CommandError(f'Formato de fecha inválido. Use DD/MM/AAAA (ej: 15/03/2024)')

        # Validar que no sea fecha futura
        if fecha_apertura > date.today():
            raise CommandError('No se puede abrir una caja en fecha futura')

        # Obtener usuario
        User = get_user_model()
        try:
            usuario = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{username}" no existe')

        # Verificar si ya existe una caja en esa fecha
        if CajaRegistradora.objects.filter(fecha_apertura__date=fecha_apertura).exists():
            raise CommandError(f'Ya existe una caja abierta en la fecha {fecha_str}')

        self.stdout.write(f'\n🔓 APERTURA DE CAJA REGISTRADORA')
        self.stdout.write(f'📅 Fecha: {fecha_apertura.strftime("%d/%m/%Y")}')
        self.stdout.write(f'👤 Usuario: {usuario.get_full_name() or usuario.username}')
        self.stdout.write('=' * 50)

        # Obtener denominaciones
        denominaciones = DenominacionMoneda.objects.all().order_by('tipo', '-valor')
        
        if not denominaciones.exists():
            raise CommandError('No hay denominaciones configuradas. Ejecute primero el setup del sistema.')

        # Separar billetes y monedas
        billetes = denominaciones.filter(tipo='BILLETE').order_by('-valor')
        monedas = denominaciones.filter(tipo='MONEDA').order_by('-valor')

        conteos_data = []
        total_inicial = Decimal('0')

        # Determinar modo: si no se especificaron cantidades específicas, usar modo interactivo
        usar_interactivo = interactivo or (billetes_str == '0,0,0,0,0,0,0' and monedas_str == '0,0,0,0,0')

        if usar_interactivo:
            # Modo interactivo (pregunta por cada denominación)
            conteos_data, total_inicial = self._modo_interactivo(billetes, monedas)
        else:
            # Modo con argumentos específicos
            conteos_data, total_inicial = self._modo_argumentos(billetes, monedas, billetes_str, monedas_str)

        # Mostrar resumen
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'💰 TOTAL INICIAL: ${int(total_inicial):,}')
        self.stdout.write('=' * 50)

        if not usar_interactivo:
            # En modo no interactivo (con argumentos específicos), crear directamente
            confirmar = True
        else:
            # En modo interactivo, pedir confirmación
            confirmar = input('\n¿Confirma la apertura de caja con estos datos? (s/N): ')
            confirmar = confirmar.lower() in ['s', 'si', 'sí', 'y', 'yes']
            
        if not confirmar:
            self.stdout.write('❌ Operación cancelada')
            return

        # Crear la caja con transacción atómica
        try:
            with transaction.atomic():
                # Importar el signal para deshabilitarlo temporalmente
                from django.db.models.signals import post_save
                from caja.models import crear_transaccion_apertura_caja
                
                # Deshabilitar el signal temporalmente
                post_save.disconnect(crear_transaccion_apertura_caja, sender='caja.CajaRegistradora')
                
                try:
                    # Crear la caja registradora SIN el signal automático
                    caja = CajaRegistradora.objects.create(
                        cajero=usuario,
                        monto_inicial=total_inicial,
                        estado='ABIERTA'
                    )
                    
                    # Actualizar la fecha de apertura manualmente después de crear
                    # (necesario porque auto_now_add no permite override)
                    from django.utils import timezone as django_timezone
                    import pytz
                    
                    # Crear datetime con timezone de Colombia
                    colombia_tz = pytz.timezone('America/Bogota')
                    fecha_datetime = colombia_tz.localize(
                        datetime.combine(fecha_apertura, datetime.min.time())
                    )
                    
                    CajaRegistradora.objects.filter(id=caja.id).update(fecha_apertura=fecha_datetime)

                    # Crear manualmente el movimiento de apertura con la fecha correcta
                    if total_inicial > 0:
                        # Obtener tipo de movimiento APERTURA
                        tipo_apertura, _ = TipoMovimiento.objects.get_or_create(
                            codigo='APERTURA',
                            defaults={
                                'nombre': 'Apertura de Caja',
                                'descripcion': 'Dinero inicial al abrir la caja',
                                'tipo_base': 'INTERNO',
                                'activo': True
                            }
                        )
                        
                        # Crear el movimiento con fecha personalizada
                        movimiento = MovimientoCaja.objects.create(
                            caja=caja,
                            tipo_movimiento=tipo_apertura,
                            tipo='INGRESO',
                            monto=total_inicial,
                            descripcion=f'Apertura de caja - Monto inicial: ${total_inicial:,.2f}',
                            usuario=usuario
                        )
                        
                        # Actualizar la fecha del movimiento - usar update directo en lugar de bulk update
                        movimiento.fecha_movimiento = fecha_datetime
                        movimiento.save(update_fields=['fecha_movimiento'])

                        # Crear la transacción en tesorería manualmente (ya que deshabilitamos el signal)
                        from caja.models import TransaccionGeneral, Cuenta
                        
                        # Obtener o crear cuenta "Caja Virtual" para tracking
                        cuenta_caja_virtual, _ = Cuenta.objects.get_or_create(
                            nombre='Caja Virtual',
                            defaults={
                                'tipo': 'RESERVA',
                                'saldo_actual': Decimal('0.00'),
                                'activo': False
                            }
                        )
                        
                        # Crear transacción en tesorería
                        transaccion = TransaccionGeneral.objects.create(
                            tipo='INGRESO',
                            monto=total_inicial,
                            descripcion=f'Apertura caja - Cajero: {usuario.username}',
                            referencia=f'APERTURA-CAJA-{caja.id}',
                            tipo_movimiento=tipo_apertura,
                            cuenta=cuenta_caja_virtual,
                            usuario=usuario
                        )
                        
                        # Actualizar la fecha de la transacción
                        transaccion.fecha = fecha_datetime
                        transaccion.save(update_fields=['fecha'])
                        
                        # Vincular movimiento y transacción
                        movimiento.transaccion_asociada = transaccion
                        movimiento.save()
                
                finally:
                    # Reactivar el signal
                    post_save.connect(crear_transaccion_apertura_caja, sender='caja.CajaRegistradora')

                # Crear conteo de apertura si hay denominaciones
                if conteos_data:
                    conteo_apertura = ConteoEfectivo.objects.create(
                        caja=caja,
                        tipo_conteo='APERTURA',
                        usuario=usuario,
                        total=total_inicial,
                        observaciones=f'Conteo de apertura - Fecha: {fecha_apertura.strftime("%d/%m/%Y")}'
                    )
                    
                    # Crear detalles del conteo
                    for conteo_data in conteos_data:
                        DetalleConteo.objects.create(
                            conteo=conteo_apertura,
                            denominacion=conteo_data['denominacion'],
                            cantidad=conteo_data['cantidad'],
                            subtotal=conteo_data['subtotal']
                        )

                # Actualizar cuenta principal si existe
                try:
                    cuenta_principal = Cuenta.objects.get(nombre='Cuenta Principal')
                    cuenta_principal.saldo += total_inicial
                    cuenta_principal.save()
                except Cuenta.DoesNotExist:
                    self.stdout.write('⚠️ Advertencia: No se encontró la cuenta principal para actualizar')

                self.stdout.write('\n✅ CAJA ABIERTA EXITOSAMENTE')
                self.stdout.write(f'📋 ID de Caja: {caja.id}')
                self.stdout.write(f'📅 Fecha: {caja.fecha_apertura.strftime("%d/%m/%Y")}')
                self.stdout.write(f'💰 Monto Inicial: ${int(caja.monto_inicial):,}')
                self.stdout.write(f'👤 Usuario: {caja.cajero.get_full_name() or caja.cajero.username}')
                
                if conteos_data:
                    self.stdout.write('\n📊 CONTEOS REGISTRADOS:')
                    for conteo_data in conteos_data:
                        denom = conteo_data['denominacion']
                        tipo_emoji = '💵' if denom.tipo == 'BILLETE' else '🪙'
                        self.stdout.write(
                            f'   {tipo_emoji} {conteo_data["cantidad"]} x ${int(denom.valor):,} = ${int(conteo_data["subtotal"]):,}'
                        )

        except Exception as e:
            raise CommandError(f'Error al crear la caja: {str(e)}')

        self.stdout.write('\n🎉 Proceso completado exitosamente!')

    def _modo_interactivo(self, billetes, monedas):
        """Modo interactivo que pregunta por cada denominación"""
        conteos_data = []
        total_inicial = Decimal('0')

        # Solicitar billetes
        if billetes.exists():
            self.stdout.write('\n💵 BILLETES:')
            self.stdout.write('-' * 30)
            for billete in billetes:
                while True:
                    try:
                        cantidad_str = input(f'¿Cuántos billetes de ${int(billete.valor):,} tiene? (0 si no tiene): ')
                        cantidad = int(cantidad_str) if cantidad_str.strip() else 0
                        if cantidad < 0:
                            self.stdout.write('❌ La cantidad no puede ser negativa')
                            continue
                        break
                    except ValueError:
                        self.stdout.write('❌ Ingrese un número válido')
                    except EOFError:
                        self.stdout.write('\n❌ Error: Entrada interrumpida')
                        raise CommandError('Modo interactivo interrumpido')
                
                if cantidad > 0:
                    subtotal = billete.valor * cantidad
                    total_inicial += subtotal
                    conteos_data.append({
                        'denominacion': billete,
                        'cantidad': cantidad,
                        'subtotal': subtotal
                    })
                    self.stdout.write(f'   ✓ {cantidad} x ${int(billete.valor):,} = ${int(subtotal):,}')

        # Solicitar monedas
        if monedas.exists():
            self.stdout.write('\n🪙 MONEDAS:')
            self.stdout.write('-' * 30)
            for moneda in monedas:
                while True:
                    try:
                        cantidad_str = input(f'¿Cuántas monedas de ${int(moneda.valor):,} tiene? (0 si no tiene): ')
                        cantidad = int(cantidad_str) if cantidad_str.strip() else 0
                        if cantidad < 0:
                            self.stdout.write('❌ La cantidad no puede ser negativa')
                            continue
                        break
                    except ValueError:
                        self.stdout.write('❌ Ingrese un número válido')
                    except EOFError:
                        self.stdout.write('\n❌ Error: Entrada interrumpida')
                        raise CommandError('Modo interactivo interrumpido')
                
                if cantidad > 0:
                    subtotal = moneda.valor * cantidad
                    total_inicial += subtotal
                    conteos_data.append({
                        'denominacion': moneda,
                        'cantidad': cantidad,
                        'subtotal': subtotal
                    })
                    self.stdout.write(f'   ✓ {cantidad} x ${int(moneda.valor):,} = ${int(subtotal):,}')

        return conteos_data, total_inicial

    def _modo_argumentos(self, billetes, monedas, billetes_str, monedas_str):
        """Modo con argumentos predefinidos"""
        conteos_data = []
        total_inicial = Decimal('0')

        try:
            # Parsear cantidades de billetes
            cantidades_billetes = [int(c.strip()) for c in billetes_str.split(',')]
            if len(cantidades_billetes) != billetes.count():
                raise CommandError(f'Se esperan {billetes.count()} cantidades de billetes, recibidas {len(cantidades_billetes)}')

            # Parsear cantidades de monedas  
            cantidades_monedas = [int(c.strip()) for c in monedas_str.split(',')]
            if len(cantidades_monedas) != monedas.count():
                raise CommandError(f'Se esperan {monedas.count()} cantidades de monedas, recibidas {len(cantidades_monedas)}')

        except ValueError:
            raise CommandError('Las cantidades deben ser números enteros válidos')

        # Procesar billetes
        self.stdout.write('\n💵 BILLETES:')
        self.stdout.write('-' * 30)
        for i, billete in enumerate(billetes):
            cantidad = cantidades_billetes[i]
            if cantidad > 0:
                subtotal = billete.valor * cantidad
                total_inicial += subtotal
                conteos_data.append({
                    'denominacion': billete,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
                self.stdout.write(f'   ✓ {cantidad} x ${int(billete.valor):,} = ${int(subtotal):,}')

        # Procesar monedas
        self.stdout.write('\n🪙 MONEDAS:')
        self.stdout.write('-' * 30)
        for i, moneda in enumerate(monedas):
            cantidad = cantidades_monedas[i]
            if cantidad > 0:
                subtotal = moneda.valor * cantidad
                total_inicial += subtotal
                conteos_data.append({
                    'denominacion': moneda,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
                self.stdout.write(f'   ✓ {cantidad} x ${int(moneda.valor):,} = ${int(subtotal):,}')

        return conteos_data, total_inicial