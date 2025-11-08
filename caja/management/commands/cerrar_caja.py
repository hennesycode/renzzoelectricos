from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone
from decimal import Decimal
import pytz
from datetime import datetime
from caja.models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento, 
    DenominacionMoneda, ConteoEfectivo, DetalleConteo,
    Cuenta, TransaccionGeneral
)


class Command(BaseCommand):
    help = 'Cierra la caja abierta con conteo de denominaciones y distribución del dinero'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que cierra la caja',
            required=True
        )
        parser.add_argument(
            '--cuanto-hay',
            type=str,
            help='Monto total real que hay en la caja (ej: 150000)',
        )
        parser.add_argument(
            '--dinero-caja',
            type=str,
            help='Dinero que se queda en la caja (ej: 50000)',
        )
        parser.add_argument(
            '--dinero-guardado',
            type=str,
            help='Dinero que se saca/guarda fuera de la caja (ej: 100000)',
        )
        parser.add_argument(
            '--observaciones',
            type=str,
            help='Observaciones del cierre',
            default=''
        )
        parser.add_argument(
            '--billetes',
            type=str,
            help='Cantidades de billetes EN CAJA separadas por comas en orden: 100k,50k,20k,10k,5k,2k,1k (ej: 0,1,0,0,0,0,0)',
            default='0,0,0,0,0,0,0'
        )
        parser.add_argument(
            '--monedas',
            type=str,
            help='Cantidades de monedas EN CAJA separadas por comas en orden: 1k,500,200,100,50 (ej: 0,0,0,0,0)',
            default='0,0,0,0,0'
        )
        parser.add_argument(
            '--interactivo',
            action='store_true',
            help='Modo interactivo (pregunta por cada denominación y datos)'
        )

    def handle(self, *args, **options):
        username = options['usuario']
        cuanto_hay_str = options.get('cuanto_hay')
        dinero_caja_str = options.get('dinero_caja')
        dinero_guardado_str = options.get('dinero_guardado')
        observaciones = options.get('observaciones', '')
        billetes_str = options['billetes']
        monedas_str = options['monedas']
        interactivo = options['interactivo']

        # Obtener usuario
        User = get_user_model()
        try:
            usuario = User.objects.get(username=username)
        except User.DoesNotExist:
            # Mostrar usuarios disponibles para ayudar
            usuarios_disponibles = User.objects.filter(is_active=True).values_list('username', flat=True)
            raise CommandError(
                f'Usuario "{username}" no existe.\n'
                f'Usuarios disponibles: {", ".join(usuarios_disponibles)}'
            )

        # Verificar que haya una caja abierta
        try:
            caja_abierta = CajaRegistradora.objects.get(estado='ABIERTA')
        except CajaRegistradora.DoesNotExist:
            raise CommandError('No hay ninguna caja abierta. No se puede cerrar.')
        except CajaRegistradora.MultipleObjectsReturned:
            raise CommandError('Error: Hay múltiples cajas abiertas. Contacte al administrador.')

        self.stdout.write(f'\n🔒 CIERRE DE CAJA REGISTRADORA')
        self.stdout.write(f'📋 Caja: #{caja_abierta.id}')
        self.stdout.write(f'📅 Fecha apertura: {caja_abierta.fecha_apertura.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write(f'💰 Monto inicial: ${int(caja_abierta.monto_inicial):,}')
        self.stdout.write(f'👤 Cajero apertura: {caja_abierta.cajero.get_full_name() or caja_abierta.cajero.username}')
        self.stdout.write(f'👤 Usuario cierre: {usuario.get_full_name() or usuario.username}')
        
        # Calcular saldo teórico de la caja
        saldo_teorico = caja_abierta.calcular_monto_sistema()
        self.stdout.write(f'💹 Saldo teórico: ${int(saldo_teorico):,}')
        self.stdout.write('=' * 70)

        # Obtener denominaciones para el conteo
        denominaciones = DenominacionMoneda.objects.all().order_by('tipo', '-valor')
        if not denominaciones.exists():
            raise CommandError('No hay denominaciones configuradas. Configure las denominaciones primero.')

        billetes = denominaciones.filter(tipo='BILLETE').order_by('-valor')
        monedas = denominaciones.filter(tipo='MONEDA').order_by('-valor')

        # Determinar modo: interactivo o con argumentos
        usar_interactivo = interactivo or not all([cuanto_hay_str, dinero_caja_str, dinero_guardado_str])

        if usar_interactivo:
            # Modo interactivo
            cuanto_hay, dinero_caja, dinero_guardado, conteos_data, observaciones = self._modo_interactivo(
                billetes, monedas, saldo_teorico, observaciones
            )
        else:
            # Modo con argumentos
            cuanto_hay, dinero_caja, dinero_guardado, conteos_data = self._modo_argumentos(
                cuanto_hay_str, dinero_caja_str, dinero_guardado_str, 
                billetes, monedas, billetes_str, monedas_str
            )

        # Validaciones finales
        diferencia = cuanto_hay - saldo_teorico

        # Mostrar resumen final
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('📊 RESUMEN DEL CIERRE:')
        self.stdout.write(f'   💹 Saldo teórico: ${int(saldo_teorico):,}')
        self.stdout.write(f'   💰 Cuánto hay realmente: ${int(cuanto_hay):,}')
        self.stdout.write(f'   📈 Diferencia: ${int(diferencia):,} {"✅" if abs(diferencia) <= 100 else "⚠️"}')
        self.stdout.write('\n📦 DISTRIBUCIÓN DEL DINERO:')
        self.stdout.write(f'   💵 Dinero en Caja: ${int(dinero_caja):,}')
        self.stdout.write(f'   🔒 Dinero Guardado: ${int(dinero_guardado):,}')
        if observaciones:
            self.stdout.write(f'   📝 Observaciones: {observaciones}')
        self.stdout.write('=' * 70)

        if usar_interactivo:
            # Pedir confirmación
            confirmar = input('\n¿Confirma el cierre de caja con estos datos? (s/N): ')
            confirmar = confirmar.lower() in ['s', 'si', 'sí', 'y', 'yes']
            
            if not confirmar:
                self.stdout.write('❌ Cierre cancelado')
                return

        # Proceder con el cierre
        try:
            with transaction.atomic():
                # Crear conteo de cierre (solo del dinero que queda en caja)
                conteo_cierre = None
                if conteos_data and dinero_caja > 0:
                    conteo_cierre = ConteoEfectivo.objects.create(
                        caja=caja_abierta,
                        tipo_conteo='CIERRE',
                        usuario=usuario,
                        total=dinero_caja,
                        observaciones=f'Conteo de cierre - {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                    )
                    
                    # Crear detalles del conteo
                    for conteo_data in conteos_data:
                        if conteo_data['cantidad'] > 0:
                            DetalleConteo.objects.create(
                                conteo=conteo_cierre,
                                denominacion=conteo_data['denominacion'],
                                cantidad=conteo_data['cantidad'],
                                subtotal=conteo_data['subtotal']
                            )

                # Cerrar la caja usando el método del modelo
                diferencia_calculada = caja_abierta.cerrar_caja(cuanto_hay, observaciones)
                
                # Guardar distribución del dinero
                caja_abierta.dinero_en_caja = dinero_caja
                caja_abierta.dinero_guardado = dinero_guardado
                caja_abierta.save()

                # Crear transacciones en tesorería para el dinero guardado
                if dinero_guardado > 0:
                    self._crear_transaccion_tesoreria(caja_abierta, dinero_guardado, usuario)

                # Mostrar resultado
                self.stdout.write('\n✅ CAJA CERRADA EXITOSAMENTE')
                self.stdout.write(f'📋 ID de Caja: {caja_abierta.id}')
                self.stdout.write(f'🕐 Fecha cierre: {caja_abierta.fecha_cierre.strftime("%d/%m/%Y %H:%M")}')
                self.stdout.write(f'💰 Monto final declarado: ${int(caja_abierta.monto_final_declarado):,}')
                self.stdout.write(f'💹 Monto final sistema: ${int(caja_abierta.monto_final_sistema):,}')
                self.stdout.write(f'📈 Diferencia: ${int(caja_abierta.diferencia):,}')
                
                if conteo_cierre:
                    self.stdout.write('\n📊 CONTEO REGISTRADO:')
                    for conteo_data in conteos_data:
                        if conteo_data['cantidad'] > 0:
                            denom = conteo_data['denominacion']
                            tipo_emoji = '💵' if denom.tipo == 'BILLETE' else '🪙'
                            self.stdout.write(
                                f'   {tipo_emoji} {conteo_data["cantidad"]} x ${int(denom.valor):,} = ${int(conteo_data["subtotal"]):,}'
                            )

                if dinero_guardado > 0:
                    self.stdout.write(f'\n🏦 ${int(dinero_guardado):,} transferidos a tesorería (Dinero Guardado)')

        except Exception as e:
            raise CommandError(f'Error al cerrar la caja: {str(e)}')

        self.stdout.write('\n🎉 Proceso de cierre completado exitosamente!')

    def _modo_interactivo(self, billetes, monedas, saldo_teorico, observaciones_inicial):
        """Modo interactivo que pregunta todos los datos paso a paso"""
        
        # 1. Preguntar cuánto hay realmente
        self.stdout.write('\n💰 DEBE HABER EN CAJA')
        self.stdout.write('-' * 40)
        
        while True:
            try:
                cuanto_hay_str = input('¿Cuánto hay realmente en la caja? $: ')
                cuanto_hay = Decimal(cuanto_hay_str.replace(',', '').replace('.', ''))
                if cuanto_hay < 0:
                    self.stdout.write('❌ El monto no puede ser negativo')
                    continue
                break
            except (ValueError, KeyboardInterrupt):
                if cuanto_hay_str.lower() in ['q', 'quit', 'salir']:
                    raise CommandError('Cierre cancelado por el usuario')
                self.stdout.write('❌ Ingrese un número válido (ej: 150000)')

        diferencia = cuanto_hay - saldo_teorico
        self.stdout.write(f'   ✓ Saldo teórico: ${int(saldo_teorico):,}')
        self.stdout.write(f'   ✓ Cuánto hay: ${int(cuanto_hay):,}')
        self.stdout.write(f'   ✓ Diferencia: ${int(diferencia):,} {"✅" if abs(diferencia) <= 100 else "⚠️"}')

        # 2. Preguntar distribución del dinero
        self.stdout.write('\n📦 DISTRIBUCIÓN DEL DINERO')
        self.stdout.write('-' * 40)
        
        while True:
            try:
                dinero_caja_str = input('💵 ¿Cuánto dinero se queda en la caja? $: ')
                dinero_caja = Decimal(dinero_caja_str.replace(',', '').replace('.', ''))
                if dinero_caja < 0:
                    self.stdout.write('❌ El monto no puede ser negativo')
                    continue
                
                dinero_guardado = cuanto_hay - dinero_caja
                self.stdout.write(f'🔒 Dinero Guardado (calculado): ${int(dinero_guardado):,}')
                
                if dinero_guardado < 0:
                    self.stdout.write('❌ El dinero en caja no puede ser mayor al total disponible')
                    continue
                    
                confirmar_dist = input('¿Es correcta esta distribución? (s/N): ')
                if confirmar_dist.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                    break
                    
            except (ValueError, KeyboardInterrupt):
                self.stdout.write('❌ Ingrese un número válido')

        # 3. Conteo de denominaciones (solo del dinero que queda en caja)
        conteos_data = []
        total_contado = Decimal('0')
        
        if dinero_caja > 0:
            self.stdout.write(f'\n💵 CONTEO DE DENOMINACIONES (Dinero en Caja: ${int(dinero_caja):,})')
            self.stdout.write('-' * 50)
            
            # Billetes
            if billetes.exists():
                self.stdout.write('\n💵 BILLETES:')
                for billete in billetes:
                    while True:
                        try:
                            cantidad_str = input(f'¿Cuántos billetes de ${int(billete.valor):,}? (0 si no tiene): ')
                            cantidad = int(cantidad_str) if cantidad_str.strip() else 0
                            if cantidad < 0:
                                self.stdout.write('❌ La cantidad no puede ser negativa')
                                continue
                            break
                        except ValueError:
                            self.stdout.write('❌ Ingrese un número válido')
                    
                    if cantidad > 0:
                        subtotal = billete.valor * cantidad
                        total_contado += subtotal
                        conteos_data.append({
                            'denominacion': billete,
                            'cantidad': cantidad,
                            'subtotal': subtotal
                        })
                        self.stdout.write(f'   ✓ {cantidad} x ${int(billete.valor):,} = ${int(subtotal):,}')

            # Monedas
            if monedas.exists():
                self.stdout.write('\n🪙 MONEDAS:')
                for moneda in monedas:
                    while True:
                        try:
                            cantidad_str = input(f'¿Cuántas monedas de ${int(moneda.valor):,}? (0 si no tiene): ')
                            cantidad = int(cantidad_str) if cantidad_str.strip() else 0
                            if cantidad < 0:
                                self.stdout.write('❌ La cantidad no puede ser negativa')
                                continue
                            break
                        except ValueError:
                            self.stdout.write('❌ Ingrese un número válido')
                    
                    if cantidad > 0:
                        subtotal = moneda.valor * cantidad
                        total_contado += subtotal
                        conteos_data.append({
                            'denominacion': moneda,
                            'cantidad': cantidad,
                            'subtotal': subtotal
                        })
                        self.stdout.write(f'   ✓ {cantidad} x ${int(moneda.valor):,} = ${int(subtotal):,}')

            # Validar que el conteo coincida con el dinero en caja
            if abs(total_contado - dinero_caja) > Decimal('1'):
                self.stdout.write(f'\n⚠️ ADVERTENCIA: El conteo (${int(total_contado):,}) no coincide exactamente con el Dinero en Caja (${int(dinero_caja):,})')
                continuar = input('¿Desea continuar de todas formas? (s/N): ')
                if not continuar.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                    raise CommandError('Cierre cancelado - El conteo debe coincidir con el dinero en caja')

        # 4. Observaciones
        if not observaciones_inicial:
            observaciones = input('\n📝 Observaciones del cierre (opcional): ').strip()
        else:
            observaciones = observaciones_inicial

        return cuanto_hay, dinero_caja, dinero_guardado, conteos_data, observaciones

    def _modo_argumentos(self, cuanto_hay_str, dinero_caja_str, dinero_guardado_str, 
                        billetes, monedas, billetes_str, monedas_str):
        """Modo con argumentos predefinidos"""
        
        try:
            cuanto_hay = Decimal(cuanto_hay_str.replace(',', '').replace('.', ''))
            dinero_caja = Decimal(dinero_caja_str.replace(',', '').replace('.', ''))
            dinero_guardado = Decimal(dinero_guardado_str.replace(',', '').replace('.', ''))
        except (ValueError, AttributeError):
            raise CommandError('Los montos deben ser números válidos')

        # Validar distribución
        if cuanto_hay != (dinero_caja + dinero_guardado):
            raise CommandError(f'La distribución no coincide: ${int(cuanto_hay):,} ≠ ${int(dinero_caja):,} + ${int(dinero_guardado):,}')

        # Procesar conteos solo si hay dinero en caja
        conteos_data = []
        if dinero_caja > 0:
            conteos_data = self._procesar_conteos_argumentos(billetes, monedas, billetes_str, monedas_str, dinero_caja)

        return cuanto_hay, dinero_caja, dinero_guardado, conteos_data

    def _procesar_conteos_argumentos(self, billetes, monedas, billetes_str, monedas_str, dinero_caja):
        """Procesa los conteos de denominaciones desde argumentos"""
        conteos_data = []
        total_contado = Decimal('0')

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
        self.stdout.write('\n💵 BILLETES EN CAJA:')
        for i, billete in enumerate(billetes):
            cantidad = cantidades_billetes[i]
            if cantidad > 0:
                subtotal = billete.valor * cantidad
                total_contado += subtotal
                conteos_data.append({
                    'denominacion': billete,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
                self.stdout.write(f'   ✓ {cantidad} x ${int(billete.valor):,} = ${int(subtotal):,}')

        # Procesar monedas
        self.stdout.write('\n🪙 MONEDAS EN CAJA:')
        for i, moneda in enumerate(monedas):
            cantidad = cantidades_monedas[i]
            if cantidad > 0:
                subtotal = moneda.valor * cantidad
                total_contado += subtotal
                conteos_data.append({
                    'denominacion': moneda,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
                self.stdout.write(f'   ✓ {cantidad} x ${int(moneda.valor):,} = ${int(subtotal):,}')

        # Validar que el conteo coincida con el dinero en caja
        if abs(total_contado - dinero_caja) > Decimal('1'):
            raise CommandError(f'El conteo (${int(total_contado):,}) no coincide con el Dinero en Caja (${int(dinero_caja):,})')

        return conteos_data

    def _crear_transaccion_tesoreria(self, caja, dinero_guardado, usuario):
        """Crea la transacción en tesorería para el dinero guardado"""
        try:
            # Obtener cuenta de reserva/dinero guardado
            cuenta_reserva = Cuenta.objects.filter(
                nombre__icontains='guardado',
                activo=True
            ).first()
            
            if not cuenta_reserva:
                # Buscar cualquier cuenta de reserva activa
                cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
            
            if not cuenta_reserva:
                self.stdout.write('⚠️ Advertencia: No se encontró cuenta de reserva para el dinero guardado')
                return

            # Obtener o crear tipo de movimiento para cierre
            tipo_cierre, _ = TipoMovimiento.objects.get_or_create(
                codigo='CIERRE_CAJA',
                defaults={
                    'nombre': 'Cierre de Caja - Dinero Guardado',
                    'descripcion': 'Dinero retirado de caja y guardado al cierre',
                    'tipo_base': 'INTERNO',
                    'activo': True
                }
            )
            
            # Crear transacción de ingreso en reserva usando la fecha de apertura de la caja
            transaccion = TransaccionGeneral.objects.create(
                tipo='INGRESO',
                monto=dinero_guardado,
                descripcion=f'Cierre caja #{caja.id} - Dinero guardado por {usuario.username}',
                referencia=f'CIERRE-{caja.id}',
                tipo_movimiento=tipo_cierre,
                cuenta=cuenta_reserva,
                usuario=usuario
            )
            
            # Actualizar la fecha de la transacción para que coincida con la fecha de apertura de la caja
            # (el cierre debe ser el mismo día que la apertura)
            colombia_tz = pytz.timezone('America/Bogota')
            fecha_caja = caja.fecha_apertura.date()
            hora_actual = datetime.now().time()
            fecha_cierre = colombia_tz.localize(
                datetime.combine(fecha_caja, hora_actual)
            )
            transaccion.fecha = fecha_cierre
            transaccion.save(update_fields=['fecha'])
            
        except Exception as e:
            self.stdout.write(f'⚠️ Advertencia: No se pudo crear transacción de tesorería: {str(e)}')