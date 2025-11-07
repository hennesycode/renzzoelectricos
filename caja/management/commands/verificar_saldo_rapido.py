from django.core.management.base import BaseCommand
from django.db import connection
from caja.models import Cuenta

class Command(BaseCommand):
    help = 'Verificación rápida del saldo bancario'

    def handle(self, *args, **options):
        self.stdout.write("🔍 VERIFICACIÓN RÁPIDA DEL SALDO")
        self.stdout.write("=" * 40)
        
        # Verificar en DB directamente
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, nombre, saldo_actual, tipo, activo FROM caja_cuenta WHERE tipo='BANCO'")
            resultado = cursor.fetchone()
        
        if resultado:
            id_cuenta, nombre, saldo, tipo, activo = resultado
            estado = "✅ ACTIVA" if activo else "❌ INACTIVA"
            
            self.stdout.write(f"💳 CUENTA: {nombre} (ID: {id_cuenta})")
            self.stdout.write(f"💰 SALDO: ${saldo:,.2f}")
            self.stdout.write(f"🏷️ TIPO: {tipo}")
            self.stdout.write(f"📊 ESTADO: {estado}")
            
            if saldo == 1340865.00:
                self.stdout.write(f"✅ EL SALDO ES CORRECTO")
                self.stdout.write(f"🌐 Ahora la web debería mostrar: ${saldo:,.2f}")
            else:
                self.stdout.write(f"❌ SALDO INCORRECTO")
        else:
            self.stdout.write(f"❌ NO SE ENCONTRÓ CUENTA BANCO")