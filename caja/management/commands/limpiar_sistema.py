from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from caja.models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento, 
    TransaccionGeneral, Cuenta
)


class Command(BaseCommand):
    help = 'Limpia todo el sistema: elimina movimientos de caja y transacciones de tesorería'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que deseas eliminar TODOS los datos del sistema',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Mostrar información del sistema
        self.stdout.write('🗑️ LIMPIAR SISTEMA COMPLETO')
        self.stdout.write('=' * 60)
        self.stdout.write('⚠️  ADVERTENCIA: Esta operación eliminará:')
        self.stdout.write('   • Todas las cajas registradoras')
        self.stdout.write('   • Todos los movimientos de caja')
        self.stdout.write('   • Todas las transacciones de tesorería')
        self.stdout.write('   • Reiniciará saldos de cuentas a $0')
        self.stdout.write('')
        self.stdout.write('✅ Se conservarán:')
        self.stdout.write('   • Usuarios del sistema')
        self.stdout.write('   • Categorías de movimientos')
        self.stdout.write('   • Configuración de cuentas')
        self.stdout.write('=' * 60)

        # Mostrar estado actual
        self._mostrar_estado_actual()

        # Mostrar usuarios disponibles
        self._mostrar_usuarios_disponibles()

        # Confirmación
        if not options.get('confirmar'):
            self.stdout.write('\n⚠️  CONFIRMACIÓN REQUERIDA')
            self.stdout.write('Esta operación NO se puede deshacer.')
            confirmar = input('\n¿Está COMPLETAMENTE SEGURO de que desea limpiar todo el sistema? (escriba "ELIMINAR TODO"): ')
            
            if confirmar != "ELIMINAR TODO":
                self.stdout.write('❌ Operación cancelada por seguridad')
                return

        # Ejecutar limpieza
        try:
            with transaction.atomic():
                self._ejecutar_limpieza()
                
            self.stdout.write('\n✅ SISTEMA LIMPIADO EXITOSAMENTE')
            self.stdout.write('🎉 El sistema está completamente limpio y listo para usar')
            
            # Mostrar estado final
            self._mostrar_estado_final()

        except Exception as e:
            raise CommandError(f'❌ Error durante la limpieza: {str(e)}')

    def _mostrar_estado_actual(self):
        """Muestra el estado actual del sistema antes de limpiar"""
        self.stdout.write('\n📊 ESTADO ACTUAL DEL SISTEMA:')
        self.stdout.write('-' * 40)
        
        # Contar registros
        cajas_count = CajaRegistradora.objects.count()
        movimientos_count = MovimientoCaja.objects.count()
        transacciones_count = TransaccionGeneral.objects.count()
        
        self.stdout.write(f'🏪 Cajas registradoras: {cajas_count}')
        self.stdout.write(f'💱 Movimientos de caja: {movimientos_count}')
        self.stdout.write(f'🏦 Transacciones tesorería: {transacciones_count}')
        
        # Mostrar saldos de cuentas
        cuentas = Cuenta.objects.all()
        self.stdout.write('\n💰 Saldos actuales:')
        for cuenta in cuentas:
            activo_str = '✅' if cuenta.activo else '❌'
            self.stdout.write(f'   {activo_str} {cuenta.nombre}: ${cuenta.saldo_actual:,.0f}')

    def _mostrar_usuarios_disponibles(self):
        """Muestra los usuarios disponibles en el sistema"""
        User = get_user_model()
        usuarios = User.objects.all().order_by('username')
        
        self.stdout.write('\n👥 USUARIOS DISPONIBLES EN EL SISTEMA:')
        self.stdout.write('-' * 40)
        
        if usuarios.exists():
            for usuario in usuarios:
                nombre_completo = usuario.get_full_name()
                if nombre_completo:
                    self.stdout.write(f'   👤 {usuario.username} - {nombre_completo}')
                else:
                    self.stdout.write(f'   👤 {usuario.username}')
                
                # Mostrar información adicional
                activo_str = '✅ Activo' if usuario.is_active else '❌ Inactivo'
                admin_str = ' (Administrador)' if usuario.is_superuser else ''
                self.stdout.write(f'      {activo_str}{admin_str}')
        else:
            self.stdout.write('   ⚠️  No hay usuarios en el sistema')

    def _ejecutar_limpieza(self):
        """Ejecuta la limpieza completa del sistema"""
        self.stdout.write('\n🗑️ INICIANDO LIMPIEZA...')
        
        # 1. Eliminar todas las cajas y sus movimientos
        cajas_eliminadas = CajaRegistradora.objects.count()
        CajaRegistradora.objects.all().delete()
        self.stdout.write(f'✅ {cajas_eliminadas} cajas registradoras eliminadas')
        
        # 2. Eliminar movimientos restantes (por si acaso)
        movimientos_eliminados = MovimientoCaja.objects.count()
        MovimientoCaja.objects.all().delete()
        self.stdout.write(f'✅ {movimientos_eliminados} movimientos de caja eliminados')
        
        # 3. Eliminar todas las transacciones de tesorería
        transacciones_eliminadas = TransaccionGeneral.objects.count()
        TransaccionGeneral.objects.all().delete()
        self.stdout.write(f'✅ {transacciones_eliminadas} transacciones de tesorería eliminadas')
        
        # 4. Reiniciar saldos de todas las cuentas a 0
        cuentas = Cuenta.objects.all()
        for cuenta in cuentas:
            cuenta.saldo_actual = Decimal('0.00')
            cuenta.save()
        self.stdout.write(f'✅ {cuentas.count()} cuentas reiniciadas a saldo $0')
        
        # 5. Mostrar lo que se conservó
        User = get_user_model()
        usuarios_count = User.objects.count()
        tipos_count = TipoMovimiento.objects.count()
        
        self.stdout.write(f'✅ {usuarios_count} usuarios conservados')
        self.stdout.write(f'✅ {tipos_count} categorías de movimiento conservadas')
        self.stdout.write(f'✅ {cuentas.count()} cuentas conservadas (saldos en $0)')

    def _mostrar_estado_final(self):
        """Muestra el estado final después de la limpieza"""
        self.stdout.write('\n📊 ESTADO FINAL DEL SISTEMA:')
        self.stdout.write('-' * 40)
        
        # Verificar que todo está limpio
        cajas_count = CajaRegistradora.objects.count()
        movimientos_count = MovimientoCaja.objects.count()
        transacciones_count = TransaccionGeneral.objects.count()
        
        self.stdout.write(f'🏪 Cajas registradoras: {cajas_count}')
        self.stdout.write(f'💱 Movimientos de caja: {movimientos_count}')
        self.stdout.write(f'🏦 Transacciones tesorería: {transacciones_count}')
        
        # Mostrar saldos (deben estar en 0)
        cuentas = Cuenta.objects.all()
        self.stdout.write('\n💰 Saldos finales:')
        for cuenta in cuentas:
            activo_str = '✅' if cuenta.activo else '❌'
            self.stdout.write(f'   {activo_str} {cuenta.nombre}: ${cuenta.saldo_actual:,.0f}')
        
        # Mostrar lo que se mantuvo
        User = get_user_model()
        usuarios_count = User.objects.count()
        tipos_count = TipoMovimiento.objects.count()
        
        self.stdout.write(f'\n✅ Sistema limpio con:')
        self.stdout.write(f'   👥 {usuarios_count} usuarios disponibles')
        self.stdout.write(f'   🏷️ {tipos_count} categorías configuradas')
        self.stdout.write(f'   🏦 {cuentas.count()} cuentas listas para usar')
        
        self.stdout.write('\n🚀 El sistema está completamente limpio y listo para comenzar de nuevo!')

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Fuerza la limpieza sin pedir confirmación (¡PELIGROSO!)',
        )